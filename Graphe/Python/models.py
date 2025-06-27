from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime


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
