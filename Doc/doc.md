# Projet Mongo DB

* Prérequis : l'intégralité du projet sera en python, et la dernière version de mongo est installée

## Partie Standalone

Avant tout je vais créer l'arborescence de mon projet, qui est très classique et conseillée :

![arbo.png](../Images/arbo.png)

Ensuite je vais créer mon utilisateurs admin pour que je puisse me connecter à ma base

```py from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")

admin = client['admin']
admin.command("createUser", "admin", pwd="adminpassword", roles=[
    {"role": "userAdminAnyDatabase", "db": "admin"},
    {"role": "readWriteAnyDatabase", "db": "admin"}
])

```
J'accorde tous les droits à cet admin.

Je crée ma base en lui donnant un nom **testdb**, et à l'intérieur une collection nommée **test**.
Ici je vais ajouter des gens avec comme informations leur nom, leur âge et leur ville.

```py from pymongo import MongoClient

client = MongoClient("mongodb://admin:adminpassword@localhost:27017/?authSource=admin")

db = client['testdb']
collection = db['test']

documents = [
    {"name" : "François", "age" : 40, "city" : "Marseille"},
    {"name" : "Marie", "age" : 23, "city" : "Toulouse"},
    {"name" : "Stéphane", "age" : 35, "city" : "Paris"},
    {"name" : "Titouan", "age" : 8, "city" : "Lyon"}
]
collection.insert_many(documents)
```

Et enfin une requête simple qui trie les résultats par odre décroissant :

```py 
results = collection.find().sort("age", -1)
for doc in results:
    print(doc)
```

On se connecte avec MongoDB Compass en local sur le port 27017 et on y retrouve notre collection et nos documents :

![mongodbcompass.png](../Images/mongodbcompass.png)

## Partie réplica set

Tout d'abord on va avoir besoin de créer nos dossiers pour nos réplicats.
Dans mon cas ils se situeront ici : "C:\mongo_replicat\rsX"

Dans un terminal en administrateur on va créer les dossiers pour les réplicats avec la commande
```shell
mkdir "C:\Program Files\MongoDB\Server\8.0\bin\mongod.exe" --replSet rs0 --dbpath C:\mongo_replicaset\rsX --port 2702X --bind_ip localhost --logpath C:\mongo_replicaset\rsX\mongo.log --logappend

```
Et ceci pour les 3

Ensuite on va créer la base primaire ici sur un port différent que celui du standalone
```py
client = MongoClient('localhost', 27021)
db = client['replitest']
collection = db['test']

doc = {"name" : "replica_test", "value" : 123}
collection.insert_one(doc)
print("Document inséré sur le primary")
```
Ensuite les replicats
```py
client = MongoClient("mongodb://localhost:27021")

config = {
    "_id": "rs0",
    "members": [
        {"_id": 0, "host": "localhost:27021"},
        {"_id": 1, "host": "localhost:27022"},
        {"_id": 2, "host": "localhost:27023"},
    ]
}

try:
    client.admin.command("replSetInitiate", config)
    print("replica initialisé")
except errors.OperationFailure as e:
    if "already initialized" in str(e):
        print("réplica déjà initialisé")
    else:
        raise

for i in range(30):
    status = client.admin.command("replSetGetStatus")
    for member in status["members"]:
        if member["name"].startswith("localhost:27021") and member["stateStr"] == "PRIMARY":
            break
    else:
        time.sleep(1)
        continue
    break
else:
    raise TimeoutError()

replica_client = MongoClient("mongodb://localhost:27021,localhost:27022,localhost:27023/?replicaSet=rs0")

db = replica_client.testdb
result = db.test.insert_one({"msg": "PRIMARY"})
print("document inséré avec l'_id :", result.inserted_id)
```

Et enfin la secondaire
```py
secondary_client = MongoClient('localhost', 27018, readPreference="secondaryPreferred")
secondary_collection = secondary_client['replitest']['test']

doc = secondary_collection.find_one({"name": "replica_test"})
print("document lu depuis secondary", doc)
```
Et c'est au moment de lancer les commandes shells et les fichiers pythons que ça ne marche pas. J'ai beau changer de port la primaire et les secondaires rien ne marche et j'en ai aucune idée.

## Intégration dans une application

Même problème qu'au dessus le serveur sur un port différent ne fonctionne pas. Uniquement le port 27017 fonctionne.

On crée un nouvel admin pour se connecter à notre base 
 ```py 
 from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27018")

db = client.admin

db.command("createUser", "admin", pwd="password123", roles=[{"role": "userAdminAnyDatabase", "db": "admin"}])
```

On crée les requêtes pour notre base 
```py 
from pymongo import MongoClient


client = MongoClient("mongodb://admin:password123@localhost:27017/admin")

db = client["ma_base"]
collection = db["utilisateurs"]

collection.insert_one({"nom": "Alice", "age": 25})

for doc in collection.find({"age": {"$gt": 20}}):
    print(doc)

collection.update_one({"nom": "Alice"}, {"$set": {"age": 26}})

collection.delete_one({"nom": "Alice"})
```
Et là avec la commande dans un terminal en administrateur
 ```shell
 "C:\Program Files\MongoDB\Server\8.0\bin\mongod.exe" --replSet rs0 --port 2702X --dbpath C:\mongo_replicaset\rsX --bind_ip localhost --logpath C:\mongo_replicaset\rsX\mongo.log --logappend
 ```

On aurait pu se connecter à notre instance sur un port choisi, démarrer un nouveau réplicat avec **rs.ininiate()**, vérifier son status avec **rs.status()** et l'ajouter avec **rs.add()**.
