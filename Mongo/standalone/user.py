from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27018/")

admin = client['admin']
admin.command("createUser", "admin", pwd="adminpassword", roles=[
    {"role": "userAdminAnyDatabase", "db": "admin"},
    {"role": "readWriteAnyDatabase", "db": "admin"}
])
