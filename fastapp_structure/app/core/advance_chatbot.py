from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.api.auth.auth import decode_token
from app.db.database import users_collection
from app.db.health_data_model import alert_collection,health_data_collection
from pydantic import BaseModel
from typing import List
from app.db.journal_model import journals_collection
from datetime import datetime, timedelta
from openai import OpenAI
# from app.auth import get_current_user
import dateparser
from bson import ObjectId   
import os
from app.core.chatbot_engine import client


from langchain_openai import ChatOpenAI, OpenAIEmbeddings  # ✅ For DeepSeek
from openai import OpenAI as OpenAIClient
from dotenv import load_dotenv
load_dotenv()
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

FAISS_FOLDER_PATH = os.path.join("data", "faiss_indexes")
client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE_URL")
)
llm = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE_URL"),
    model=os.getenv("OPENAI_API_MODEL")
)

# Extract natural language date from query
def extract_date_from_question(text: str):
    parsed = dateparser.parse(text, settings={
        "PREFER_DATES_FROM": "past",
        "RELATIVE_BASE": datetime.utcnow(),
        "DATE_ORDER": "DMY"
    })
    if parsed:
        return parsed.date().isoformat()
    return None

# Determine if the query is personal
def is_personal_query(query: str) -> bool:
    personal_keywords = ["my", "me", "mine", "i", "today", "yesterday", "last"]
    return any(kw in query.lower() for kw in personal_keywords)

# Fetch all user data for a date
def fetch_user_context(username: str, query: str) -> List[str]:
    target_date = extract_date_from_question(query) or datetime.utcnow().date().isoformat()
    context = []

    journal = journals_collection.find_one({"username": username, "date": target_date})
    if journal:
        context.append(f"📓 Journal: {journal.get('text', '')}")

    alerts = list(alert_collection.find({"username": username, "date": target_date}))
    for alert in alerts:
        context.append(f"🚨 Alert: {alert.get('message', '')}")

    notifications = users_collection.find_one({"username": username}).get("notifications", [])
    for note in notifications:
        context.append(f"🔔 Notification: {note.get('text', '')}")

    metrics = list(health_data_collection.find({"username": username, "metric": "heart_rate", "timestamp": {"$regex": target_date}}))
    for m in metrics:
        context.append(f"📊 Heart rate: {m['value']} bpm at {m['timestamp']}")

    return context

# Heart rate summary

def get_steps_data(username: str, days=7):
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    query = {
        "username": username,
        "metric": "steps",
        "timestamp": {"$gte": start, "$lte": end}
    }
    return list(health_data_collection.find(query))

def summarize_steps(entries: List[dict]) -> str:
    if not entries:
        return "I couldn’t find any step data for you in the past 7 days."
    values = [e["value"] for e in entries]
    avg = sum(values) / len(values)
    total = sum(values)
    return (
        f"🚶 Steps Summary 🚶"
        f"You walked a total of **{total} steps** over the past 7 days, averaging **{avg:.0f} steps/day**."
        f"Keep it up, or try to aim for a bit more if you're targeting 7,000+ daily!"
    )

def get_spo2_data(username: str, days=7):
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    query = {
        "username": username,
        "metric": "spo2",
        "timestamp": {"$gte": start, "$lte": end}
    }
    return list(health_data_collection.find(query))

def summarize_spo2(entries: List[dict]) -> str:
    if not entries:
        return "I couldn’t find any SpO₂ data for you in the past 7 days."
    values = [e["value"] for e in entries]
    avg = sum(values) / len(values)
    min_val = min(values)
    return (
        f"🫁 Oxygen Saturation (SpO₂) 🫁"
        f"Your average SpO₂ over the past 7 days is **{avg:.1f}%**."
        f"Lowest recorded was **{min_val}%**."
        f"If you're often below 94%, you may want to consult a health professional."
    )

def get_heart_rate_data(username: str, days=7):
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    query = {
        "username": username,
        "metric": "heart_rate",
        "timestamp": {"$gte": start, "$lte": end}
    }
    return list(health_data_collection.find(query))

def summarize_heart_rate(entries: List[dict]) -> str:
    if not entries:
        return "I couldn’t find any heart rate data for you in the past 7 days."
    values = [e["value"] for e in entries]
    avg = sum(values) / len(values)
    max_val = max(values)
    min_val = min(values)
    highest = next(e for e in entries if e["value"] == max_val)
    lowest = next(e for e in entries if e["value"] == min_val)
    fmt = lambda dt: dt.strftime("%b %d at %H:%M")
    return (
        f"💡Health Insight💡\n\n"
        f"Your average heart rate over the past 7 days is **{avg:.1f} bpm**.\n"
        f"- 🔺 Highest: **{max_val} bpm** on {fmt(highest['timestamp'])}\n"
        f"- 🔻 Lowest: **{min_val} bpm** on {fmt(lowest['timestamp'])}\n\n"
        f"This looks {'normal' if avg < 85 else 'a bit elevated'} — let me know if you'd like a weekly comparison!"
    )

# RAG helpers

def normalize(text: str) -> str:
    return text.strip()

def apply_personality(raw_answer: str, mode: str) -> str:
    mode = mode.lower()
    if mode == "krishna":
        return (
            "🌸 Wisdom from the Bhagavad Gita 🌸\n\n"
            f"🕉️ {raw_answer}\n\n"
            "Let us reflect on this divine insight as Lord Krishna guides us."
        )
    else:
        return (
            "💡Health Insight💡\n\n"
            f"{raw_answer}\n\n"
            "Let me know if you have any more health-related questions!"
        )

def choose_best_answer(user_query: str, candidates: List[str]) -> str:
    if not candidates:
        return "⚠️ No answers to evaluate."

    system_prompt = (
        "You are a smart medical assistant. Given a user's health-related question and a list of candidate answers, "
        "choose the most relevant and medically accurate one. Return only that answer."
    )

    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_API_MODEL"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"User Question: {user_query}\n\n" + "\n\n---\n\n".join(candidates)},
                {"role": "user", "content": "Choose the most relevant answer."}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("GPT ranking failed:", e)
        return candidates[0]

# Route 1: Static heart rate insight
