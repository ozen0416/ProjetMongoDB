# Projet BDD Graphe

* Prérequis : installation de Neo4j Desktop et de Docker Desktop

On va créer un fichier yml avec le service neo4j.

Ensuite on va créer nos fichiers pythons pour que le projet fonctionne.
Notamment les fichiers de connexions à la base de donnée, les requirements ou l'api.

Nous allons voir quelques fichiers important pour le projet.

Tout d'abord la configuration de la base de donnée :
```python
@dataclass
class Neo4jConfig:
    uri: str = "bolt://localhost:7687"
    username: str = "neo4j"
    password: str = "motdepasse123"
    database: str = "neo4j"
```
Un simple fichier qui nous permet de renseigner les informations pour la connexion à la base de donnée.

Ensuite on va créer les commandes, clients et produits :
```python
@dataclass
class Client:
    nom: str
    email: str
    date_inscription: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nom": self.nom,
            "email": self.email,
            "date_inscription": self.date_inscription.isoformat()
        }


@dataclass
class Produit:
    nom: str
    prix: float
    categorie: str
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nom": self.nom,
            "prix": self.prix,
            "categorie": self.categorie,
            "description": self.description
        }


@dataclass
class Commande:
    id_commande: str
    date_commande: datetime
    montant_total: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id_commande": self.id_commande,
            "date_commande": self.date_commande.isoformat(),
            "montant_total": self.montant_total
        }
```
Enfin les requêtes. Voici quelques exemples :
```python
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
```

```python
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
```
Ensuite on créé l'api avec FastAPI.

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Optional
import logging
from database import Neo4jConnection
from queries import Neo4jQueries
from config import Neo4jConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClientResponse(BaseModel):
    nom: str
    email: EmailStr


class ProduitResponse(BaseModel):
    produit: str
    prix: float
    categorie: str
    quantite: int
    prix_unitaire: float
    commande: str
    date_commande: str


class SuggestionResponse(BaseModel):
    produit: str
    categorie: str
    prix: float
    description: str
    popularite: int
    prix_moyen: float


app = FastAPI(
    title="API Neo4j E-commerce",
    description="API REST pour interagir avec une base de données Neo4j d'e-commerce",
    version="1.0.0"
)

neo4j_connection = None
queries = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global neo4j_connection, queries
    try:
        config = Neo4jConfig()
        neo4j_connection = Neo4jConnection(config)
        driver = neo4j_connection.connect()
        queries = Neo4jQueries(driver)
        logging.info("API démarrée avec succès")
        yield
    finally:
        if neo4j_connection:
            neo4j_connection.close()
            logging.info("Connexion fermée proprement")

app = FastAPI(
    title="API Neo4j E-commerce",
    description="API REST pour interagir avec une base de données Neo4j d'e-commerce",
    version="1.0.0",
    lifespan=lifespan
)


def get_queries() -> Neo4jQueries:
    if queries is None:
        raise HTTPException(status_code=500, detail="Service de base de données non disponible")
    return queries


@app.get("/", summary="Page d'accueil")
async def root():
    return {"message": "API Neo4j E-commerce", "version": "1.0.0", "status": "active"}


@app.get("/stats", summary="Statistiques générales")
async def get_statistiques(queries: Neo4jQueries = Depends(get_queries)):
    try:
        stats = queries.get_statistiques_generales()
        return JSONResponse(content=stats)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des statistiques: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")


@app.get("/clients/{email}/produits",
         response_model=List[ProduitResponse],
         summary="Produits achetés par un client")
async def get_produits_client(
        email: EmailStr,
        queries: Neo4jQueries = Depends(get_queries)
):
    try:
        produits = queries.get_produits_par_client(str(email))
        if not produits:
            raise HTTPException(
                status_code=404,
                detail=f"Aucun produit trouvé pour le client {email}"
            )
        return produits
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des produits pour {email}: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")


@app.get("/clients/{email}/suggestions",
         response_model=List[SuggestionResponse],
         summary="Suggestions de produits pour un client")
async def get_suggestions_client(
        email: EmailStr,
        limite: Optional[int] = 5,
        queries: Neo4jQueries = Depends(get_queries)
):
    try:
        if limite <= 0 or limite > 20:
            raise HTTPException(
                status_code=400,
                detail="La limite doit être entre 1 et 20"
            )

        suggestions = queries.get_suggestions_produits(str(email), limite)
        if not suggestions:
            return []

        return suggestions
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la génération de suggestions pour {email}: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")


@app.get("/produits/{nom_produit}/clients",
         response_model=List[ClientResponse],
         summary="Clients ayant acheté un produit")
async def get_clients_produit(
        nom_produit: str,
        queries: Neo4jQueries = Depends(get_queries)
):
    try:
        clients = queries.get_clients_par_produit(nom_produit)
        if not clients:
            raise HTTPException(
                status_code=404,
                detail=f"Aucun client trouvé pour le produit '{nom_produit}'"
            )
        return clients
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des clients pour {nom_produit}: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")


@app.get("/produits/{nom_produit}/commandes",
         summary="Commandes contenant un produit")
async def get_commandes_produit(
        nom_produit: str,
        queries: Neo4jQueries = Depends(get_queries)
):
    try:
        commandes = queries.get_commandes_avec_produit(nom_produit)
        if not commandes:
            raise HTTPException(
                status_code=404,
                detail=f"Aucune commande trouvée pour le produit '{nom_produit}'"
            )
        return JSONResponse(content=commandes)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des commandes pour {nom_produit}: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

```

Visualisation du graphe :
```txt
+----------------+         A_EFFECTUÉ        +----------------+        CONTIENT        +----------------+
|    Client      |-------------------------> |   Commande     |---------------------->|    Produit     |
+----------------+                          +----------------+                       +----------------+
| nom            |                          | id_commande    |                       | nom            |
| email          |                          | date_commande  |                       | prix           |
| date_inscription|                         | montant_total  |                       | catégorie      |
+----------------+                          +----------------+                       | description    |
                                                                                     +----------------+
```
Pour lancer le projet, d'abord installer le *requirement.txt*.
```bash
pip install -r requirements.txt
```
Ensuite lancer le .yml dans le dossier prévu.
```bash
docker compose up -d
```
Ensuite initialiser les données avec :
```bash
pyton main.py
```
Et enfin l'api :
```bash
uvicorn api:app --reload
```
On va retrouver toutes nos informations sur l'adresse suivant
```txt
http://localhost:8000/docs
```