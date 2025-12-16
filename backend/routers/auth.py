from fastapi import APIRouter, HTTPException
from backend.database import get_db_connection
from backend.schemas import UserRegister, UserLogin, TokenResponse
from backend.security import get_password_hash, verify_password, create_access_token
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", status_code=201)
def register(user: UserRegister):
    db = get_db_connection()
    
    if db["users"].find_one({"$or": [{"email": user.email}, {"username": user.username}]}):
        raise HTTPException(status_code=409, detail="User with this email or username already exists")

    new_user = {
        "username": user.username,
        "email": user.email,
        "password_hash": get_password_hash(user.password),
        "full_name": user.full_name,
        "role": "user",
        "created_at": datetime.utcnow().isoformat(),
        "is_active": True
    }
    
    result = db["users"].insert_one(new_user)
    
    return {
        "code": 201,
        "message": "User registered successfully",
        "user_id": str(result.inserted_id),
        "email": new_user["email"],
        "role": new_user["role"]
    }

@router.post("/login", response_model=TokenResponse)
def login(creds: UserLogin):
    db = get_db_connection()
    user = db["users"].find_one({"username": creds.username})
    
    if not user or not verify_password(creds.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account disabled")

    access_token = create_access_token(data={"sub": str(user["_id"]), "role": user["role"]})

    return {
        "code": 200,
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 60 * 60,
        "user": {
            "user_id": str(user["_id"]),
            "username": user["username"],
            "role": user["role"]
        }
    }

