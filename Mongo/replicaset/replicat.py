from pymongo import MongoClient, errors
import time

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
