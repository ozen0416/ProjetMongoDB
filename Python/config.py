from dataclasses import dataclass

@dataclass
class Neo4jConfig:
    uri: str = "bolt://localhost:7687"
    username: str = "neo4j"
    password: str = "motdepasse123"
    database: str = "neo4j"
