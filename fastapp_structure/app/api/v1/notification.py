from fastapi import APIRouter, Depends, HTTPException, Body, Query
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import random
import openai  # ✅ Required for GPT

from app.api.v1.auth import decode_token
from app.db.database import users_collection


router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# ✅ Conversation state store
@router.get("/get_notification")
def get_notifications(token: str = Depends(oauth2_scheme)):
    valid, username = decode_token(token)
    if not valid:
        raise HTTPException(status_code=401, detail=username)

    user = users_collection.find_one({"username": username}, {"notifications": 1})
    return user.get("notifications", [])


@router.post("/mark_notification_read")
def mark_read(index: int = Body(...), token: str = Depends(oauth2_scheme)):
    valid, username = decode_token(token)
    if not valid:
        raise HTTPException(status_code=401, detail=username)

    users_collection.update_one(
        {"username": username},
        {"$set": {f"notifications.{index}.read": True}}
    )
    return {"message": "Marked as read"}



@router.get("/notifications/unread")
def get_unread_notifications(token: str = Depends(oauth2_scheme)):
    valid, username = decode_token(token)
    if not valid:
        raise HTTPException(status_code=401, detail=username)

    user = users_collection.find_one({"username": username}, {"notifications": 1})
    all_notifications = user.get("notifications", [])
    unread = [n for n in all_notifications if not n.get("read", False)]

    return {
        "count": len(unread),
        "notifications": unread
    }

