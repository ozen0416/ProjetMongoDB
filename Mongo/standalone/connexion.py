from pymongo import MongoClient

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

results = collection.find().sort("age", -1)
for doc in results:
    print(doc)
