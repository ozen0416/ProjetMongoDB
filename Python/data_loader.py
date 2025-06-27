from neo4j import Driver
from models import Client, Produit, Commande
from typing import List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DataLoader:
    def __init__(self, driver: Driver):
        self.driver = driver

    def create_constraints_and_indexes(self):
        constraints_queries = [
            "CREATE CONSTRAINT client_email_unique IF NOT EXISTS FOR (c:Client) REQUIRE c.email IS UNIQUE",
            "CREATE CONSTRAINT commande_id_unique IF NOT EXISTS FOR (cmd:Commande) REQUIRE cmd.id_commande IS UNIQUE",
            "CREATE CONSTRAINT produit_nom_unique IF NOT EXISTS FOR (p:Produit) REQUIRE p.nom IS UNIQUE"
        ]

        index_queries = [
            "CREATE INDEX client_nom_index IF NOT EXISTS FOR (c:Client) ON (c.nom)",
            "CREATE INDEX produit_categorie_index IF NOT EXISTS FOR (p:Produit) ON (p.categorie)",
            "CREATE INDEX commande_date_index IF NOT EXISTS FOR (cmd:Commande) ON (cmd.date_commande)"
        ]

        with self.driver.session() as session:
            for query in constraints_queries + index_queries:
                try:
                    session.run(query)
                    logger.info(f"Exécution réussie: {query}")
                except Exception as e:
                    logger.warning(f"Contrainte/Index probablement existant: {e}")

    def load_clients_bulk(self, clients: List[Client]):
        clients_data = [client.to_dict() for client in clients]

        query = """
        UNWIND $clients as client_data
        MERGE (c:Client {email: client_data.email})
        SET c.nom = client_data.nom,
            c.date_inscription = datetime(client_data.date_inscription)
        """

        with self.driver.session() as session:
            result = session.run(query, clients=clients_data)
            logger.info(f"Clients créés: {result.consume().counters.nodes_created}")

    def load_produits_bulk(self, produits: List[Produit]):
        produits_data = [produit.to_dict() for produit in produits]

        query = """
        UNWIND $produits as produit_data
        MERGE (p:Produit {nom: produit_data.nom})
        SET p.prix = produit_data.prix,
            p.categorie = produit_data.categorie,
            p.description = produit_data.description
        """

        with self.driver.session() as session:
            result = session.run(query, produits=produits_data)
            logger.info(f"Produits créés: {result.consume().counters.nodes_created}")

    def load_commandes_bulk(self, commandes: List[Commande]):
        commandes_data = [commande.to_dict() for commande in commandes]

        query = """
        UNWIND $commandes as commande_data
        MERGE (cmd:Commande {id_commande: commande_data.id_commande})
        SET cmd.date_commande = datetime(commande_data.date_commande),
            cmd.montant_total = commande_data.montant_total
        """

        with self.driver.session() as session:
            result = session.run(query, commandes=commandes_data)
            logger.info(f"Commandes créées: {result.consume().counters.nodes_created}")

    def create_client_commande_relations(self, relations_data: List[dict]):
        query = """
        UNWIND $relations as rel
        MATCH (c:Client {email: rel.client_email})
        MATCH (cmd:Commande {id_commande: rel.commande_id})
        MERGE (c)-[r:A_EFFECTUÉ]->(cmd)
        SET r.date = datetime(rel.date)
        """

        with self.driver.session() as session:
            result = session.run(query, relations=relations_data)
            logger.info(f"Relations A_EFFECTUÉ créées: {result.consume().counters.relationships_created}")

    def create_commande_produit_relations(self, relations_data: List[dict]):
        query = """
        UNWIND $relations as rel
        MATCH (cmd:Commande {id_commande: rel.commande_id})
        MATCH (p:Produit {nom: rel.produit_nom})
        MERGE (cmd)-[r:CONTIENT]->(p)
        SET r.quantite = rel.quantite,
            r.prix_unitaire = rel.prix_unitaire
        """

        with self.driver.session() as session:
            result = session.run(query, relations=relations_data)
            logger.info(f"Relations CONTIENT créées: {result.consume().counters.relationships_created}")


def create_sample_data():
    clients = [
        Client("Alice Martin", "alice@email.com", datetime(2023, 1, 15)),
        Client("Bob Dupont", "bob@email.com", datetime(2023, 2, 20)),
        Client("Claire Moreau", "claire@email.com", datetime(2023, 3, 10)),
        Client("David Bernard", "david@email.com", datetime(2023, 4, 5))
    ]

    produits = [
        Produit("Laptop Pro", 1299.99, "Informatique", "Ordinateur portable haute performance"),
        Produit("Smartphone X", 799.99, "Téléphonie", "Smartphone dernière génération"),
        Produit("Casque Audio", 199.99, "Audio", "Casque sans fil premium"),
        Produit("Tablette Plus", 599.99, "Informatique", "Tablette tactile 10 pouces"),
        Produit("Montre Connect", 299.99, "Accessoires", "Montre intelligente connectée")
    ]

    commandes = [
        Commande("CMD001", datetime(2023, 5, 1), 1499.98),
        Commande("CMD002", datetime(2023, 5, 3), 799.99),
        Commande("CMD003", datetime(2023, 5, 7), 899.98),
        Commande("CMD004", datetime(2023, 5, 10), 1599.97)
    ]

    relations_client_commande = [
        {"client_email": "alice@email.com", "commande_id": "CMD001", "date": "2023-05-01T10:30:00"},
        {"client_email": "bob@email.com", "commande_id": "CMD002", "date": "2023-05-03T14:15:00"},
        {"client_email": "claire@email.com", "commande_id": "CMD003", "date": "2023-05-07T09:45:00"},
        {"client_email": "david@email.com", "commande_id": "CMD004", "date": "2023-05-10T16:20:00"}
    ]

    relations_commande_produit = [
        {"commande_id": "CMD001", "produit_nom": "Laptop Pro", "quantite": 1, "prix_unitaire": 1299.99},
        {"commande_id": "CMD001", "produit_nom": "Casque Audio", "quantite": 1, "prix_unitaire": 199.99},
        {"commande_id": "CMD002", "produit_nom": "Smartphone X", "quantite": 1, "prix_unitaire": 799.99},
        {"commande_id": "CMD003", "produit_nom": "Tablette Plus", "quantite": 1, "prix_unitaire": 599.99},
        {"commande_id": "CMD003", "produit_nom": "Montre Connect", "quantite": 1, "prix_unitaire": 299.99},
        {"commande_id": "CMD004", "produit_nom": "Laptop Pro", "quantite": 1, "prix_unitaire": 1299.99},
        {"commande_id": "CMD004", "produit_nom": "Montre Connect", "quantite": 1, "prix_unitaire": 299.99}
    ]

    return clients, produits, commandes, relations_client_commande, relations_commande_produit
