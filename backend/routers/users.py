from fastapi import APIRouter, Depends, HTTPException, Query
from backend.database import get_db_connection
from backend.deps import get_current_user_claims, require_admin
from backend.schemas import UserUpdate, UserRoleUpdate, UserResponse
from bson.objectid import ObjectId
from datetime import datetime

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("", dependencies=[Depends(require_admin)])
def list_users(page: int = 1, limit: int = 20, role: str = None):
    db = get_db_connection()
    query = {}
    if role:
        query["role"] = role
    
    skip = (page - 1) * limit
    users_cursor = db["users"].find(query).skip(skip).limit(limit)
    users = []
    
    for u in users_cursor:
        users.append({
            "user_id": str(u["_id"]),
            "username": u["username"],
            "email": u["email"],
            "full_name": u.get("full_name", ""),
            "role": u["role"],
            "created_at": u.get("created_at")
        })
        
    return {"code": 200, "data": users, "page": page, "limit": limit}

@router.get("/{user_id}", response_model=UserResponse)
def get_user_profile(user_id: str, claims: dict = Depends(get_current_user_claims)):

    if claims["role"] != "admin" and claims["sub"] != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    db = get_db_connection()
    try:
        user = db["users"].find_one({"_id": ObjectId(user_id)})
    except:
        raise HTTPException(status_code=404, detail="Invalid ID format")

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "code": 200,
        "user_id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "full_name": user.get("full_name", ""),
        "role": user["role"],
        "created_at": user.get("created_at", "")
    }

@router.put("/{user_id}")
def update_user_profile(user_id: str, update_data: UserUpdate, claims: dict = Depends(get_current_user_claims)):

    if claims["role"] != "admin" and claims["sub"] != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
        
    db = get_db_connection()
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    
    if not update_dict:
        raise HTTPException(status_code=400, detail="No data provided")

    result = db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
        
    return {"code": 200, "message": "Profile updated successfully"}

@router.delete("/{user_id}")
def delete_user(user_id: str, claims: dict = Depends(get_current_user_claims)):
    if claims["role"] != "admin" and claims["sub"] != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
        
    db = get_db_connection()

    result = db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_active": False, "deleted_at": datetime.utcnow().isoformat()}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
        
    return {"code": 200, "message": "User account deactivated", "timestamp": datetime.utcnow().isoformat()}

@router.put("/{user_id}/role", dependencies=[Depends(require_admin)])
def update_user_role(user_id: str, role_data: UserRoleUpdate):
    if role_data.role not in ["user", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")
        
    db = get_db_connection()
    result = db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"role": role_data.role}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
        
    return {"code": 200, "message": f"Role updated to {role_data.role}"}