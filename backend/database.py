from pymongo import MongoClient
import os

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://admin:password123@mongo:27017/"
)

DB_NAME = os.getenv("DB_NAME", "dota_project")

def get_db_connection():
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]
