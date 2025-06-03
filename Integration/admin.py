from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27018")

db = client.admin

db.command("createUser", "admin", pwd="password123", roles=[{"role": "userAdminAnyDatabase", "db": "admin"}])

