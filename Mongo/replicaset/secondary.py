from pymongo import MongoClient, ReadPreference

secondary_client = MongoClient('localhost', 27018, readPreference="secondaryPreferred")
secondary_collection = secondary_client['replitest']['test']

doc = secondary_collection.find_one({"name": "replica_test"})
print("document lu depuis secondary", doc)