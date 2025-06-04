
from pymongo import MongoClient
from datetime import datetime, timezone
from app.db.database import MONGO_URL

client = MongoClient(MONGO_URL)
db = client["techjewel"]
health_data_collection = db["health_data_entries"]

def estimate_calories(steps, duration_min, weight_kg=70):
    steps_per_min = steps / duration_min if duration_min else 0
    if steps_per_min > 100:
        met = 6.0
    elif steps_per_min > 60:
        met = 3.5
    else:
        met = 1.5
    return round(met * weight_kg * (duration_min / 60), 2)

def save_health_data(username: str, payload: dict):
    now = datetime.utcnow().replace(tzinfo=timezone.utc)
    docs = []

    steps_data = payload.get("steps", {})
    calories_data = {}

    # Auto-calculate calories from step deltas
    sorted_steps = sorted(steps_data.items())
    for i in range(1, len(sorted_steps)):
        ts_prev, val_prev = sorted_steps[i - 1]
        ts_now, val_now = sorted_steps[i]

        t1 = datetime.fromisoformat(ts_prev)
        t2 = datetime.fromisoformat(ts_now)
        duration = (t2 - t1).seconds / 60
        steps_diff = max(0, val_now - val_prev)
        kcal = estimate_calories(steps_diff, duration)
        calories_data[ts_now] = kcal

    for metric in ["steps", "heartRate", "spo2", "sleep"]:
        metric_data = payload.get(metric, {})
        for ts, val in metric_data.items():
            docs.append({
                "username": username,
                "metric": metric,
                "timestamp": datetime.fromisoformat(ts),
                "value": val,
                "created_at": now
            })

    for ts, val in calories_data.items():
        docs.append({
            "username": username,
            "metric": "calories",
            "timestamp": datetime.fromisoformat(ts),
            "value": val,
            "created_at": now
        })

    if docs:
        health_data_collection.insert_many(docs)

def get_health_data_by_range(username: str, start: datetime, end: datetime):
    return list(health_data_collection.find({
        "username": username,
        "timestamp": {"$gte": start, "$lte": end}
    }).sort("timestamp", 1))


def get_metric_summary(username, metric, start: datetime, end: datetime):
    pipeline = [
        {"$match": {
            "username": username,
            "timestamp": {"$gte": start, "$lte": end},
            "metric": metric
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
            return entry["value"] if entry["metric"] == "steps" else 0
        elif metric == "heartRate":
            return entry["value"] if entry["metric"] == "heartRate" else 0
        elif metric == "spo2":
            return round(entry["value"] * 100, 2) if entry["metric"] == "spo2" else 0
        elif metric == "sleep":
            return entry["value"] if entry["metric"] == "sleep" else 0
        elif metric == "calories":
            return entry["value"] if entry["metric"] == "calories" else 0
    except:
        return None
    
    
