import requests
from pymongo import MongoClient
import time

# Configuració
MONGO_URI = "mongodb://admin:password123@localhost:27017/"
DB_NAME = "dota_project"

def get_database():
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]

def sync_countries():
    print("Fetching RestCountries data...")
    try:
        headers = { "User-Agent": "Mozilla/5.0 (DotaProject/1.0)" }
        url = "https://restcountries.com/v3.1/all?fields=name,cca2,cca3,population,region,subregion,latlng"
        
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Error API RestCountries: {response.status_code}")
            return

        countries_data = response.json()
        db = get_database()
        collection = db["countries"]
        
        count = 0
        for c in countries_data:
            doc = {
                "code": c["cca2"],         # Clau per OpenDota (ES) es per a fer un "pont" entre World Bank que utilitza codi de 3 lletres i OpenDota que utilitza de 2
                "code3": c.get("cca3"),    # Clau per World Bank (ESP)
                "name": c["name"]["common"],
                "population": c.get("population", 0),
                "region": c.get("region", "Unknown"),
                "subregion": c.get("subregion", "Unknown"),
                "latlng": c.get("latlng", [0, 0])
            }
            collection.update_one({"code": doc["code"]}, {"$set": doc}, upsert=True)
            count += 1
            
        print(f"Saved/Updated {count} countries (with ISO-3 codes).")
        
    except Exception as e:
        print(f"Error fetching countries: {e}")

def sync_worldbank_data():
    print("Fetching World Bank Data (GDP & Internet)...")
    db = get_database()
    countries_collection = db["countries"]
    
    indicators = {
        "gdp": "NY.GDP.PCAP.CD",
        "internet": "IT.NET.USER.ZS"
    }
    
    for key, indicator_code in indicators.items():
        try:
            print(f"   ↳ Fetching {key} ({indicator_code})...")
           
            url = f"http://api.worldbank.org/v2/country/all/indicator/{indicator_code}?format=json&per_page=300&mrv=1"
            
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Error fetching WB {key}")
                continue
                
            data = response.json()
            if len(data) < 2: 
                continue
                
            wb_records = data[1]
            
            updates = 0
            for record in wb_records:
                country_iso3 = record.get("countryiso3code", "")
                value = record.get("value")
                
                if country_iso3 and value is not None:
                    
                    result = countries_collection.update_one(
                        {"code3": country_iso3},
                        {"$set": {key: value}}
                    )
                    if result.modified_count > 0:
                        updates += 1
                        
            print(f"      Updated {updates} countries with {key} data.")
            
        except Exception as e:
            print(f"Error in WB sync ({key}): {e}")

def sync_dota_players():
    print("Fetching OpenDota Pro Players...")
    try:
        response = requests.get("https://api.opendota.com/api/proPlayers")
        players_data = response.json()
        db = get_database()
        collection = db["players"]
        
        count = 0
        for p in players_data:
            if not p.get("loccountrycode"): continue
            doc = {
                "account_id": p["account_id"],
                "name": p.get("name"),
                "team_name": p.get("team_name"),
                "fantasy_role": p.get("fantasy_role"),
                "country_code": p["loccountrycode"].upper(),
                "last_match_time": p.get("last_match_time")
            }
            collection.update_one({"account_id": doc["account_id"]}, {"$set": doc}, upsert=True)
            count += 1
        print(f"Saved/Updated {count} pro players.")
    except Exception as e:
        print(f"Error fetching players: {e}")

if __name__ == "__main__":
    print("Starting ETL Process...")
    sync_countries()      
    sync_worldbank_data()
    sync_dota_players() 
    print("ETL Process Finished.")