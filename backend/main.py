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
# 1. THE "PRO-GAMER DENSITY" RANKING
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
    """
    Returns the distribution of player roles (Position 1-5) across different regions.
    """
    db = get_db_connection()

    pipeline = [
        {
            "$lookup": {
                "from": "countries",
                "localField": "country_code",
                "foreignField": "code",
                "as": "c"
            }
        },
        { "$unwind": "$c" },

        {
            "$addFields": {
                "normalized_role": {
                    "$cond": [
                        { "$in": ["$fantasy_role", [0, None]] },
                        None,
                        "$fantasy_role"
                    ]
                }
            }
        },

        {
            "$group": {
                "_id": {
                    "region": "$c.region",
                    "role": "$normalized_role"
                },
                "count": { "$sum": 1 }
            }
        },

        { "$sort": { "_id.region": 1, "_id.role": 1 } }
    ]

    raw_data = list(db["players"].aggregate(pipeline))

    def get_role_name(role_num):
        role_map = {
            1: "Position 1 (Carry)",
            2: "Position 2 (Mid)",
            3: "Position 3 (Offlane)",
            4: "Position 4 (Soft Support)",
            5: "Position 5 (Hard Support)",
            None: "Unknown/Unspecified"
        }
        return role_map.get(role_num, "Unknown/Unspecified")

    formatted = {}

    for item in raw_data:
        region = item["_id"]["region"]
        role_num = item["_id"]["role"]
        role_name = get_role_name(role_num)

        if region not in formatted:
            formatted[region] = {}

        formatted[region][role_name] = item["count"]

    result = {}
    for region, roles in formatted.items():
        total = sum(roles.values())

        result[region] = {
            "roles": roles,
            "total_players": total,
            "percentages": {
                role: round((count / total * 100), 2)
                for role, count in roles.items()
            }
        }

    return result

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
      
        { "$match": { "c.latlng": { "$exists": True, "$ne": [] } } },
        { "$project": {
            "_id": 0,
            "name": "$name",
            "country": "$c.name",
            "coordinates": "$c.latlng" 
        }},
        { "$limit": 1000 }
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

# ---------------------------------------------------------
# 6. WEALTH CORRELATION (Economics)
# Goal: Demostrar que Dota 2 és popular en economies emergents/mitjanes
# ---------------------------------------------------------
@app.get("/analytics/correlation/wealth")
def get_wealth_correlation():
    db = get_db_connection()
    pipeline = [
        { "$group": { "_id": "$country_code", "player_count": {"$sum": 1} } },
        
        { "$lookup": { "from": "countries", "localField": "_id", "foreignField": "code", "as": "c" } },
        { "$unwind": "$c" },
        
        { "$match": { 
            "c.gdp": { "$exists": True, "$ne": None },
            "c.population": { "$gt": 1000000 } 
        }},

        { "$project": {
            "_id": 0,
            "country": "$c.name",
            "code": "$_id",
            "gdp_per_capita": "$c.gdp",    
            "total_players": "$player_count", 
            "players_per_million": {       
                "$multiply": [
                    { "$divide": ["$player_count", "$c.population"] },
                    1000000
                ]
            }
        }},
    
        { "$sort": { "gdp_per_capita": -1 } }
    ]
    return list(db["players"].aggregate(pipeline))


# ---------------------------------------------------------
# 7. INFRASTRUCTURE CORRELATION (Technology)
# Goal: Demostrar la barrera d'entrada tecnològica
# ---------------------------------------------------------
@app.get("/analytics/correlation/internet")
def get_internet_correlation():
    db = get_db_connection()
    pipeline = [
        { "$group": { "_id": "$country_code", "player_count": {"$sum": 1} } },
        { "$lookup": { "from": "countries", "localField": "_id", "foreignField": "code", "as": "c" } },
        { "$unwind": "$c" },
        
        { "$match": { 
            "c.internet": { "$exists": True, "$ne": None },
            "c.population": { "$gt": 1000000 } 
        }},

        { "$project": {
            "_id": 0,
            "country": "$c.name",
            "code": "$_id",
            "internet_access_percent": "$c.internet",
            "players_per_million": {                  
                "$multiply": [
                    { "$divide": ["$player_count", "$c.population"] },
                    1000000
                ]
            }
        }},
        
        { "$sort": { "internet_access_percent": 1 } }
    ]
    return list(db["players"].aggregate(pipeline))


# ---------------------------------------------------------
# 8. COUNTRY YOUNG POPULATION CORRELATION
# Goal:Obtenir la correlació entre la població jove (15-24 anys) i els jugadors professionals per a un país específic
# ---------------------------------------------------------
@app.get("/analytics/country/{country_name}/youth-correlation")
def get_country_youth_correlation(country_name: str):
    db = get_db_connection()
    
    country = db["countries"].find_one(
        {"name": {"$regex": f"^{country_name}$", "$options": "i"}}
    )
    
    if not country:
        raise HTTPException(status_code=404, detail=f"Country '{country_name}' not found")
    
    player_count = db["players"].count_documents({"country_code": country["code"]})
    
    pop_15_24 = country.get("pop_15_24_total")
    young_pop_percent = country.get("young_population_percent")
    
    if pop_15_24 is None:
        raise HTTPException(
            status_code=404, 
            detail=f"Young population data not available for {country['name']}. Run the ETL script to fetch this data."
        )
    
    total_population = country.get("population", 0)
    players_per_million = (player_count / total_population * 1000000) if total_population > 0 else 0
    players_per_100k_youth = (player_count / pop_15_24 * 100000) if pop_15_24 > 0 else 0
    
    return {
        "country": country["name"],
        "country_code": country["code"],
        "region": country.get("region", "Unknown"),
        "demographics": {
            "total_population": total_population,
            "young_population_15_24": int(pop_15_24),
            "young_population_15_19": int(country.get("pop_15_19_total", 0)),
            "young_population_20_24": int(country.get("pop_20_24_total", 0)),
            "young_population_percent": young_pop_percent
        },
        "pro_players": {
            "total_count": player_count,
            "players_per_million_population": round(players_per_million, 2),
            "players_per_100k_youth": round(players_per_100k_youth, 2)
        },
        "correlation_insight": {
            "youth_ratio": f"{young_pop_percent}% of population is aged 15-24",
            "player_youth_ratio": f"{player_count} pro players for {int(pop_15_24):,} young adults (15-24 years)",
            "interpretation": _get_correlation_interpretation(players_per_100k_youth, young_pop_percent)
        }
    }

def _get_correlation_interpretation(players_per_100k_youth: float, young_pop_percent: float):
    """Helper function to provide interpretation of the correlation"""
    if players_per_100k_youth > 10:
        return "Very high pro player density among youth population"
    elif players_per_100k_youth > 5:
        return "High pro player density among youth population"
    elif players_per_100k_youth > 1:
        return "Moderate pro player density among youth population"
    elif players_per_100k_youth > 0.1:
        return "Low pro player density among youth population"
    else:
        return "Very low or no pro player presence among youth population"