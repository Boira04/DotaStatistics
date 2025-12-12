import requests
from pymongo import MongoClient
import os
import time

MONGO_URI = "mongodb://admin:password123@localhost:27017/"
DB_NAME = "dota_project"

def get_database():
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]

def sync_countries():
    print("Fetching Countries data...")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(
            "https://restcountries.com/v3.1/all?fields=name,cca2,population,region,subregion,latlng", 
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"Error API RestCountries. Status: {response.status_code}")
            print(f"Response: {response.text[:100]}") 
            return

        countries_data = response.json()
        
        if not isinstance(countries_data, list):
            print("Error: API has not returned a list of countries")
            return
            
        print(f"Data recieved: {len(countries_data)} countries found")

        db = get_database()
        collection = db["countries"]
        
        count = 0
        for c in countries_data:
            if "cca2" not in c:
                continue

            doc = {
                "code": c["cca2"],
                "name": c["name"]["common"],
                "population": c.get("population", 0),
                "region": c.get("region", "Unknown"),
                "subregion": c.get("subregion", "Unknown"),
                "latlng": c.get("latlng", [0, 0])
            }
            
            collection.update_one(
                {"code": doc["code"]}, 
                {"$set": doc}, 
                upsert=True
            )
            count += 1
            
        print(f"Saved/Updated {count} countries successfully.")
        
    except Exception as e:
        print(f"CRITICAL Error fetching countries: {e}")

def sync_dota_players():
    print("Fetching OpenDota Pro Players...")
    try:
        response = requests.get("https://api.opendota.com/api/proPlayers")
        players_data = response.json()
        
        db = get_database()
        collection = db["players"]
        
        count = 0
        for p in players_data:
            if not p.get("loccountrycode"):
                continue
                
            country_code = p["loccountrycode"].upper()
            
            doc = {
                "account_id": p["account_id"],
                "name": p.get("name"),
                "team_name": p.get("team_name"),
                "fantasy_role": p.get("fantasy_role"), 
                "country_code": country_code,
                "last_match_time": p.get("last_match_time")
            }
            
            collection.update_one(
                {"account_id": doc["account_id"]}, 
                {"$set": doc}, 
                upsert=True
            )
            count += 1
            
        print(f"Saved/Updated {count} pro players.")

    except Exception as e:
        print(f"Error fetching players: {e}")

if __name__ == "__main__":
    print("Starting ETL Process...")
    sync_countries()
    sync_dota_players()
    print("ETL Process Finished.")