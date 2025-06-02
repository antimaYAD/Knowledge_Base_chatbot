from pymongo import MongoClient
from datetime import datetime,timedelta
from bson import ObjectId
import os
from app.db.database import MONGO_URL
from pymongo import DESCENDING
from datetime import timezone

client = MongoClient(MONGO_URL)
db = client["techjewel"]
health_data_collection = db["health_data_entries"]

# data["timestamp"] = datetime.utcnow().replace(tzinfo=UTC)

def save_health_data(username: str, data: dict):
    data["username"] = username
    # data["timestamp"] = datetime.utcnow().replace(tzinfo=UTC)
    data["timestamp"] = datetime.utcnow().replace(tzinfo=timezone.utc)

    health_data_collection.insert_one(data)


def get_health_data_by_range(username: str, start: datetime, end: datetime):
    return list(health_data_collection.find({
        "username": username,
        "timestamp": {"$gte": start, "$lte": end}
    }))

# def get_health_data_by_range(username: str, start: datetime, end: datetime):
#     return list(health_data_collection.find({"username": username}))


def get_metric_summary(username, metric, start: datetime, end: datetime):
    pipeline = [
        {"$match": {
            "username": username,
            "timestamp": {"$gte": start, "$lte": end},
            f"{metric}.records": {"$exists": True}
        }},
        {"$unwind": f"${metric}.records"},
        {"$project": {
            "value": {
                "$cond": [
                    {"$eq": [metric, "heartRate"]}, "$heartRate.records.beatsPerMinute",
                    {"$cond": [
                        {"$eq": [metric, "spo2"]}, "$spo2.records.percentage",
                        {"$cond": [
                            {"$eq": [metric, "steps"]}, "$steps.records.count",
                            "$sleep.duration"
                        ]}
                    ]}
                ]
            }
        }},
        {"$group": {
            "_id": None,
            "min": {"$min": "$value"},
            "max": {"$max": "$value"},
            "avg": {"$avg": "$value"},
            "total": {"$sum": "$value"},
            "count": {"$sum": 1}
        }}
    ]
    result = list(health_data_collection.aggregate(pipeline))
    return result[0] if result else None




def extract_metric_value(entry, metric):
    try:
        if metric == "steps":
            return entry["steps"].get("today", 0)
        elif metric == "heartRate":
            return entry["heartRate"]["latest"]["beatsPerMinute"]
        elif metric == "spo2":
            return round(entry["spo2"]["latest"]["percentage"] * 100, 2)
        elif metric == "sleep":
            return entry["sleep"]["duration"]
    except:
        return None
