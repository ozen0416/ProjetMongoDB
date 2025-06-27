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
