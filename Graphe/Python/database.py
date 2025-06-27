from neo4j import GraphDatabase
from config import Neo4jConfig
import logging

logger = logging.getLogger(__name__)


class Neo4jConnection:
    def __init__(self, config: Neo4jConfig):
        self.config = config
        self.driver = None

    def connect(self):
        try:
            self.driver = GraphDatabase.driver(
                self.config.uri,
                auth=(self.config.username, self.config.password)
            )
            self.driver.verify_connectivity()
            logger.info("Connexion à Neo4j établie avec succès")
            return self.driver
        except Exception as e:
            logger.error(f"Erreur de connexion à Neo4j: {e}")
            raise

    def close(self):
        if self.driver:
            self.driver.close()
            logger.info("Connexion Neo4j fermée")
