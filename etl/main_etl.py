import requests
from pymongo import MongoClient
import time
import os

# Configuració
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_URI = f"mongodb://admin:password123@{MONGO_HOST}:27017/" # Usa MONGO_HOST aquí
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
                "code": c["cca2"],          # Clau per OpenDota (ES) es per a fer un "pont" entre World Bank que utilitza codi de 3 lletres i OpenDota que utilitza de 2
                "code3": c.get("cca3"),     # Clau per World Bank (ESP)
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
    print("Fetching World Bank Data (GDP, Internet & Young Population)...")
    db = get_database()
    countries_collection = db["countries"]
    
    indicators = {
        "gdp": "NY.GDP.PCAP.CD",
        "internet": "IT.NET.USER.ZS",
        "pop_1519_male": "SP.POP.1519.MA",
        "pop_1519_female": "SP.POP.1519.FE",
        "pop_2024_male": "SP.POP.2024.MA",
        "pop_2024_female": "SP.POP.2024.FE"
    }
    
    for key, indicator_code in indicators.items():
        try:
            print(f"   ↳ Fetching {key} ({indicator_code})...")
           
            url = f"http://api.worldbank.org/v2/country/all/indicator/{indicator_code}?format=json&per_page=300&mrv=1"
            
            response = requests.get(url)
            if response.status_code != 200:
                print(f"      ERROR: API returned status {response.status_code}")
                continue
                
            data = response.json()
            if len(data) < 2: 
                print(f"      WARNING: No data available")
                continue
                
            wb_records = data[1]
            
            if not wb_records:
                print(f"      WARNING: Empty records list")
                continue
            
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
                        
            print(f"      Updated {updates} countries")
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"      ERROR: {e}")

    print("   ↳ Aggregating young population (15-24 years)...")
    try:
        countries = countries_collection.find({
            "population": {"$gt": 0}
        })
        
        updated = 0
        for country in countries:
            pop_1519_male = country.get("pop_1519_male", 0) or 0
            pop_1519_female = country.get("pop_1519_female", 0) or 0
            pop_2024_male = country.get("pop_2024_male", 0) or 0
            pop_2024_female = country.get("pop_2024_female", 0) or 0
            
            pop_1519_total = pop_1519_male + pop_1519_female
            pop_2024_total = pop_2024_male + pop_2024_female
            pop_1524_total = pop_1519_total + pop_2024_total
            
            if pop_1524_total > 0:
                total_pop = country.get("population", 0)
                young_pop_percent = (pop_1524_total / total_pop * 100) if total_pop > 0 else 0
                
                countries_collection.update_one(
                    {"_id": country["_id"]},
                    {"$set": {
                        "pop_15_19_total": pop_1519_total,
                        "pop_20_24_total": pop_2024_total,
                        "pop_15_24_total": pop_1524_total,
                        "young_population_percent": round(young_pop_percent, 2)
                    }}
                )
                updated += 1
        
        print(f"      Calculated metrics for {updated} countries")
        
    except Exception as e:
        print(f"      ERROR: {e}")

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
    print("\n" + "="*60)
    print("STARTING ETL PROCESS")
    print("="*60 + "\n")
    
    sync_countries()
    print()
    sync_worldbank_data()
    print()
    sync_dota_players()
    
    print("\n" + "="*60)
    print("ETL PROCESS FINISHED")
