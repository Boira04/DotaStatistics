from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from backend.database import get_db_connection

app = FastAPI(
    title="Dota 2 Country Analytics API",
    description="Backend for Distributed Computing Project 2",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "online", "system": "Dota 2 Analytics Platform"}

# ---------------------------------------------------------
# 1. THE "PRO-GAMER DENSITY" RANKING (Ja el tenies)
# ---------------------------------------------------------
@app.get("/analytics/density/rankings")
def get_density_rankings(limit: int = 10):
    db = get_db_connection()
    pipeline = [
        { "$group": { "_id": "$country_code", "player_count": {"$sum": 1} } },
        { "$lookup": { "from": "countries", "localField": "_id", "foreignField": "code", "as": "country_info" } },
        { "$unwind": "$country_info" },
        { "$match": { "country_info.population": { "$gt": 100000 } } },
        { "$project": {
            "country": "$country_info.name",
            "code": "$_id",
            "players": "$player_count",
            "population": "$country_info.population",
            "density_per_million": { "$multiply": [ { "$divide": ["$player_count", "$country_info.population"] }, 1000000 ] }
        }},
        { "$sort": { "density_per_million": -1 } },
        { "$limit": limit }
    ]
    return list(db["players"].aggregate(pipeline))

# ---------------------------------------------------------
# 2. REGIONAL ROLE DISTRIBUTION
# Goal: Saber si Europa juga més de "Support" o "Core"
# ---------------------------------------------------------
@app.get("/analytics/regions/roles")
def get_regional_roles():
    db = get_db_connection()
    pipeline = [
        # 1. Unim jugadors amb països per saber la Regió
        { "$lookup": { "from": "countries", "localField": "country_code", "foreignField": "code", "as": "c" } },
        { "$unwind": "$c" },
        # 2. Agrupem per Regió i Rol (1=Carry/Mid, 2=Support)
        { "$group": {
            "_id": { "region": "$c.region", "role": "$fantasy_role" },
            "count": { "$sum": 1 }
        }},
        # 3. Ordenem per regió
        { "$sort": { "_id.region": 1 } }
    ]
    # Processar resultats per fer-los més llegibles al frontend
    raw_data = list(db["players"].aggregate(pipeline))
    
    # Formategem la resposta: { "Europe": {"Core": 120, "Support": 90}, ... }
    formatted = {}
    for item in raw_data:
        region = item["_id"]["region"]
        role_num = item["_id"]["role"]
        role_name = "Core" if role_num == 1 else "Support" if role_num == 2 else "Flex/Unknown"
        
        if region not in formatted:
            formatted[region] = {}
        formatted[region][role_name] = item["count"]
        
    return formatted

# ---------------------------------------------------------
# 3. GLOBAL HEATMAP DATA
# Goal: Retornar coordenades per pintar un mapa
# ---------------------------------------------------------
@app.get("/analytics/map/distribution")
def get_heatmap_data():
    db = get_db_connection()
    pipeline = [
        { "$lookup": { "from": "countries", "localField": "country_code", "foreignField": "code", "as": "c" } },
        { "$unwind": "$c" },
        # Només volem coordenades vàlides
        { "$match": { "c.latlng": { "$exists": True, "$ne": [] } } },
        { "$project": {
            "_id": 0,
            "name": "$name",
            "country": "$c.name",
            "coordinates": "$c.latlng" # [lat, lng]
        }},
        { "$limit": 1000 } # Limitem per no saturar el mapa
    ]
    return list(db["players"].aggregate(pipeline))

# ---------------------------------------------------------
# 4. THE "UNTAPPED MARKET" FINDER
# Goal: Països GRANS (> 20M hab) amb ZERO jugadors pros
# ---------------------------------------------------------
@app.get("/analytics/insights/market-gaps")
def get_market_gaps():
    db = get_db_connection()
    # Aquí comencem des de la col·lecció COUNTRIES
    pipeline = [
        { "$match": { "population": { "$gt": 20000000 } } }, # Països grans
        { "$lookup": {
            "from": "players",
            "localField": "code",
            "foreignField": "country_code",
            "as": "pro_players"
        }},
        # Filtrem els que tenen l'array de jugadors buit o molt petit
        { "$match": { "pro_players": { "$size": 0 } } },
        { "$project": {
            "_id": 0,
            "country": "$name",
            "code": "$code",
            "population": "$population",
            "region": "$region",
            "message": "High potential market, 0 pro players found."
        }},
        { "$sort": { "population": -1 } }
    ]
    return list(db["countries"].aggregate(pipeline))

# ---------------------------------------------------------
# 5. SUBREGION DOMINANCE
# Goal: Quina subregió (Eastern Europe vs SE Asia) domina?
# ---------------------------------------------------------
@app.get("/analytics/regions/dominance")
def get_subregion_dominance():
    db = get_db_connection()
    pipeline = [
        { "$lookup": { "from": "countries", "localField": "country_code", "foreignField": "code", "as": "c" } },
        { "$unwind": "$c" },
        { "$group": {
            "_id": "$c.subregion",
            "total_players": { "$sum": 1 }
        }},
        { "$sort": { "total_players": -1 } }
    ]
    return list(db["players"].aggregate(pipeline))