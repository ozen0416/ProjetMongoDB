from pymongo import MongoClient


client = MongoClient("mongodb://admin:password123@localhost:27017/admin")

db = client["ma_base"]
collection = db["utilisateurs"]

collection.insert_one({"nom": "Alice", "age": 25})

for doc in collection.find({"age": {"$gt": 20}}):
    print(doc)

collection.update_one({"nom": "Alice"}, {"$set": {"age": 26}})

collection.delete_one({"nom": "Alice"})
