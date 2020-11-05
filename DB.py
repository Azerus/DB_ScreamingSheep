import os
from pymongo import MongoClient


cluster = MongoClient(str(os.environ.get('DB')))
db = cluster["discord"]
collection = db["user_data"]