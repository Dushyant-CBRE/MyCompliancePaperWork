from fastapi import APIRouter, HTTPException
from typing import List
from app.models.user import User
from app.data.users import USERS

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=List[User])
def get_all_users():
    """Return all users."""
    return USERS


@router.get("/{user_id}", response_model=User)
def get_user_by_id(user_id: int):
    """Return a single user by ID."""
    user = next((u for u in USERS if u.id == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")
    return user
