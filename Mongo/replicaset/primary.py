from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client['replitest']
collection = db['test']

doc = {"name" : "replica_test", "value" : 123}
collection.insert_one(doc)
print("Document inséré sur le primary")