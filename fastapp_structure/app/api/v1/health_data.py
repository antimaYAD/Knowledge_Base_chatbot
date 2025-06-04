# app/api/v1/routes/health_data.py
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timedelta
from app.api.v1.auth import decode_token
from app.db.health_data_model import get_health_data_by_range,save_health_data,get_metric_summary, extract_metric_value
from fastapi.security import OAuth2PasswordBearer
from typing import Optional, Union, List
from pydantic import BaseModel
from bson import ObjectId
from typing import Dict


router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class HealthPayload(BaseModel):
    steps: Dict[str, int] = {}
    heartRate: Dict[str, int] = {}
    spo2: Dict[str, float] = {}
    sleep: Dict[str, int] = {}

@router.post("/health/save")
def save(payload: HealthPayload, token: str = Depends(oauth2_scheme)):
    valid, username = decode_token(token)
    if not valid:
        raise HTTPException(status_code=401, detail=username)
    save_health_data(username, payload.dict())
    return {"message": "Saved"}



@router.get("/health/summary")
def get_metric_summary_api(
    metric: str = Query(..., enum=["heartRate", "spo2", "steps", "sleep","calories"]),
    mode: str = Query(..., enum=["daily", "weekly", "monthly","yearly"]),
    token: str = Depends(oauth2_scheme)
):
    valid, username = decode_token(token)
    if not valid:
        raise HTTPException(status_code=401, detail=username)

    now = datetime.utcnow()
    if mode == "daily":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif mode == "weekly":
        start = now - timedelta(days=7)
    elif mode == "monthly":
        start = now - timedelta(days=30)
    elif mode == "yearly":
        start = now - timedelta(days=365)
    else:
        raise HTTPException(status_code=400, detail="Invalid mode")

    end = now
    summary = get_metric_summary(username, metric, start, end)
    if not summary:
        return {"message": "No data found"}
    return {"metric": metric, "mode": mode, "summary": summary}




@router.get("/health/graph-data")
def get_graph_data_api(
    metric: str = Query(..., enum=["steps", "heartRate", "spo2", "sleep","calories"]),
    mode: str = Query(..., enum=["daily", "weekly", "monthly", "yearly"]),
    token: str = Depends(oauth2_scheme)
):
    valid, username = decode_token(token)
    if not valid:
        raise HTTPException(status_code=401, detail=username)

    now = datetime.utcnow()

    if mode == "daily":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        group_by = "%H:%M"
    elif mode == "weekly":
        start = now - timedelta(days=7)
        group_by = "%Y-%m-%d"
    elif mode == "monthly":
        start = now - timedelta(days=30)
        group_by = "%Y-%m-%d"
    elif mode == "yearly":
        start = now - timedelta(days=365 * 5)  # up to 5 years history
        group_by = "%Y"
    else:
        raise HTTPException(status_code=400, detail="Invalid mode")

    records = get_health_data_by_range(username, start, now)

    grouped = {}
    for entry in records:
        ts = entry["timestamp"].astimezone().strftime(group_by)
        if ts not in grouped:
            grouped[ts] = []
        value = extract_metric_value(entry, metric)
        if value is not None:
            grouped[ts].append(value)

    graph_data = []
    for label, values in sorted(grouped.items()):
        y = sum(values) if metric in ["steps", "sleep"] else round(sum(values) / len(values), 2)
        graph_data.append({"x": label, "y": y})

    return {"graph": graph_data}
