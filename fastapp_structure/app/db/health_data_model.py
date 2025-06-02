from pymongo import MongoClient
from datetime import datetime,timedelta
from bson import ObjectId
import os
from app.db.database import MONGO_URL
from pymongo import DESCENDING

client = MongoClient(MONGO_URL)
db = client["techjewel"]
health_data_collection = db["health_data_entries"]


def save_health_data(username: str, data: dict):
    data["username"] = username
    data["timestamp"] = datetime.utcnow()
    health_data_collection.insert_one(data)


# def get_health_data_by_range(username: str, start: datetime, end: datetime):
#     return list(health_data_collection.find({
#         "username": username,
#         "timestamp": {"$gte": start, "$lte": end}
#     }))

def get_health_data_by_range(username: str, start: datetime, end: datetime):
    return list(health_data_collection.find({"username": username}))
