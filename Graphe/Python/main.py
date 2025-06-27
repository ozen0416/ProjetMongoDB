import logging
from database import Neo4jConnection
from data_loader import DataLoader, create_sample_data
from config import Neo4jConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    try:
        config = Neo4jConfig()
        connection = Neo4jConnection(config)
        driver = connection.connect()

        loader = DataLoader(driver)

        logger.info("Création des contraintes et index...")
        loader.create_constraints_and_indexes()

        logger.info("Génération des données d'exemple...")
        clients, produits, commandes, rel_client_cmd, rel_cmd_produit = create_sample_data()

        logger.info("Chargement des clients...")
        loader.load_clients_bulk(clients)

        logger.info("Chargement des produits...")
        loader.load_produits_bulk(produits)

        logger.info("Chargement des commandes...")
        loader.load_commandes_bulk(commandes)

        logger.info("Création des relations client-commande...")
        loader.create_client_commande_relations(rel_client_cmd)

        logger.info("Création des relations commande-produit...")
        loader.create_commande_produit_relations(rel_cmd_produit)

        logger.info("Données chargées avec succès!")

        connection.close()

    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation: {e}")
        raise


if __name__ == "__main__":
    main()
