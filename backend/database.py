# app/database.py
from pymongo import MongoClient
import os

# Si estem dins de Docker, el host és 'mongo', si estem en local, és 'localhost'
# Això permet que funcioni tant al teu PC com quan ho despleguis al núvol.
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_URI = f"mongodb://admin:password123@{MONGO_HOST}:27017/"
DB_NAME = "dota_project"

def get_db_connection():
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]