from fastapi import APIRouter, Depends, HTTPException, Body, Query
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import random
from openai import OpenAI

from app.api.v1.auth import decode_token
from app.db.database import users_collection
from app.db.health_data_model import alert_collection
from bson import ObjectId
import os
from app.core.chatbot_engine import client
from dotenv import load_dotenv
load_dotenv()


router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

client = client or OpenAI(api_key=os.getenv("OPENAI_API_KEY"),base_url=os.getenv("OPENAI_API_BASE_URL"))


class AlertResponseRequest(BaseModel):
    response: str

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


@router.post("/alerts/{alert_id}/response")
def save_alert_response(
    alert_id: str,
    req: AlertResponseRequest,
    token: str = Depends(oauth2_scheme)
):
    valid, username = decode_token(token)
    if not valid:
        raise HTTPException(status_code=401, detail="Unauthorized")

    alert = alert_collection.find_one({"_id": ObjectId(alert_id), "username": username})
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Initialize chat if missing
    chat = alert.get("chat", [])
    if not chat:
        chat = [{"role": "assistant", "content": alert.get("message", "Let’s talk about your health alert.")}]
        alert_collection.update_one({"_id": ObjectId(alert_id)}, {"$set": {"chat": chat}})

    # Limit to 4 user turns (8 messages total including assistant)
    user_turns = len([m for m in chat if m["role"] == "user"])
    if user_turns >= 4:
        return {"message": "✅ Conversation ended after 4 rounds.", "assistant_reply": None}

    # Add user message
    user_msg = {"role": "user", "content": req.response}
    alert_collection.update_one(
        {"_id": ObjectId(alert_id)},
        {
            "$push": {"chat": user_msg},
            "$set": {
                "responded": True,
                "responded_at": datetime.utcnow()
            }
        }
    )

    chat.append(user_msg)  

    try:
        gpt_response = client.chat.completions.create(
            model=os.getenv("OPENAI_API_MODEL"),
            messages=chat,
            max_tokens=100,
            temperature=0.8
        )
        assistant_msg = gpt_response.choices[0].message.content.strip()
    except Exception as e:
        print("⚠️ GPT continuation failed:", e)
        assistant_msg = "Thanks for your response. We'll keep monitoring your health."

    # Save assistant reply
    assistant_entry = {"role": "assistant", "content": assistant_msg}
    alert_collection.update_one(
        {"_id": ObjectId(alert_id)},
        {"$push": {"chat": assistant_entry}}
    )

    return {
        "message": "Response saved.",
        "assistant_reply": assistant_msg
    }