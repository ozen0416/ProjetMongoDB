from neo4j import Driver
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class Neo4jQueries:
    def __init__(self, driver: Driver):
        self.driver = driver

    def get_produits_par_client(self, email_client: str) -> List[Dict[str, Any]]:
        query = """
        MATCH (c:Client {email: $email})-[:A_EFFECTUÉ]->(cmd:Commande)-[cont:CONTIENT]->(p:Produit)
        RETURN p.nom as produit, p.prix as prix, p.categorie as categorie,
               cont.quantite as quantite, cont.prix_unitaire as prix_unitaire,
               cmd.id_commande as commande, cmd.date_commande as date_commande
        ORDER BY cmd.date_commande DESC
        """

        with self.driver.session() as session:
            result = session.run(query, email=email_client)
            return [record.data() for record in result]

    def get_clients_par_produit(self, nom_produit: str) -> List[Dict[str, Any]]:
        query = """
        MATCH (c:Client)-[:A_EFFECTUÉ]->(cmd:Commande)-[:CONTIENT]->(p:Produit {nom: $produit})
        RETURN c.nom as client, c.email as email, 
               cmd.id_commande as commande, cmd.date_commande as date_commande
        ORDER BY cmd.date_commande DESC
        """

        with self.driver.session() as session:
            result = session.run(query, produit=nom_produit)
            return [record.data() for record in result]

    def get_commandes_avec_produit(self, nom_produit: str) -> List[Dict[str, Any]]:
        query = """
        MATCH (cmd:Commande)-[cont:CONTIENT]->(p:Produit {nom: $produit})
        MATCH (c:Client)-[:A_EFFECTUÉ]->(cmd)
        RETURN cmd.id_commande as commande, cmd.date_commande as date_commande,
               cmd.montant_total as montant_total, c.nom as client,
               cont.quantite as quantite, cont.prix_unitaire as prix_unitaire
        ORDER BY cmd.date_commande DESC
        """

        with self.driver.session() as session:
            result = session.run(query, produit=nom_produit)
            return [record.data() for record in result]

    def get_suggestions_produits(self, email_client: str, limite: int = 5) -> List[Dict[str, Any]]:
        query = """
        MATCH (client:Client {email: $email})-[:A_EFFECTUÉ]->(:Commande)-[:CONTIENT]->(produit:Produit)
        WITH client, collect(produit) as produits_client

        MATCH (autre_client:Client)-[:A_EFFECTUÉ]->(:Commande)-[:CONTIENT]->(produit_commun:Produit)
        WHERE autre_client <> client AND produit_commun IN produits_client
        WITH client, produits_client, autre_client, count(produit_commun) as produits_communs
        ORDER BY produits_communs DESC

        MATCH (autre_client)-[:A_EFFECTUÉ]->(:Commande)-[:CONTIENT]->(suggestion:Produit)
        WHERE NOT suggestion IN produits_client
        WITH suggestion, count(DISTINCT autre_client) as popularite, 
             avg(suggestion.prix) as prix_moyen

        RETURN suggestion.nom as produit, suggestion.categorie as categorie,
               suggestion.prix as prix, suggestion.description as description,
               popularite, prix_moyen
        ORDER BY popularite DESC, prix_moyen ASC
        LIMIT $limite
        """

        with self.driver.session() as session:
            result = session.run(query, email=email_client, limite=limite)
            return [record.data() for record in result]

    def get_statistiques_generales(self) -> Dict[str, Any]:
        query = """
        MATCH (c:Client) WITH count(c) as nb_clients
        MATCH (cmd:Commande) WITH nb_clients, count(cmd) as nb_commandes
        MATCH (p:Produit) WITH nb_clients, nb_commandes, count(p) as nb_produits
        MATCH (:Client)-[:A_EFFECTUÉ]->(:Commande)-[:CONTIENT]->(:Produit)
        WITH nb_clients, nb_commandes, nb_produits, count(*) as nb_achats
        MATCH (cmd:Commande)
        RETURN nb_clients, nb_commandes, nb_produits, nb_achats,
               avg(cmd.montant_total) as montant_moyen_commande,
               sum(cmd.montant_total) as chiffre_affaires_total
        """

        with self.driver.session() as session:
            result = session.run(query)
            return result.single().data()
