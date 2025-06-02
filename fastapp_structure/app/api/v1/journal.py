from pydantic import BaseModel
from typing import Optional, Union, List
from app.db.journal_model import save_journal_entry
from app.db.database import users_collection
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from app.api.v1.auth import decode_token
from app.utils.journal_prompt_generator import generate_journal_prompt
from datetime import datetime, timedelta
from fastapi import Query
from app.db.journal_model import get_journals_by_user_month, get_journals_by_day,patch_journal
from app.utils.journal_summary_generator import summarize_journals
from datetime import time ,datetime


router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class RichJournalEntry(BaseModel):
    type: str  # "triggered" or "scheduled"
    prompt: str
    response: str
    feeling_now: str
    feeling_most_of_day: Union[str, List[str]]
    triggered_by: Union[str, List[str]]
    expressed_to: Union[str, List[str]]
    body_reaction: Union[str, List[str]]
    note: Optional[str] = None
    tags: Optional[List[str]] = []



class PromptRequest(BaseModel):
    type: str  # "triggered" or "scheduled"
    mood: Optional[str] = None
    health_data: Optional[dict] = None  # keys: spo2, heart_rate, sleep


class PatchJournalRequest(BaseModel):
    journal_id: str
    response: Optional[str] = None
    feeling_now: Optional[str] = None
    feeling_most_of_day: Optional[Union[str, List[str]]] = None
    triggered_by: Optional[Union[str, List[str]]] = None
    expressed_to: Optional[Union[str, List[str]]] = None
    body_reaction: Optional[Union[str, List[str]]] = None
    note: Optional[str] = None
    tags: Optional[List[str]] = None


    

@router.post("/journal/save-detailed")
def save_rich_journal(req: RichJournalEntry, token: str = Depends(oauth2_scheme)):
    valid, username = decode_token(token)
    if not valid:
        raise HTTPException(status_code=401, detail=username)

    extra_fields = {
        "feeling_now": req.feeling_now,
        "feeling_most_of_day": req.feeling_most_of_day,
        "triggered_by": req.triggered_by,
        "expressed_to": req.expressed_to,
        "body_reaction": req.body_reaction,
        "note": req.note
    }

    today = datetime.utcnow().date()
    user = users_collection.find_one({"username": username})
    last_date = user.get("last_journal_date")
    current_streak = user.get("streak", 0)

    if last_date == today:
        pass  # Already journaled today
    elif last_date == today - timedelta(days=1):
        current_streak += 1
    else:
        current_streak = 1  # Reset

    users_collection.update_one(
        {"username": username},
        {"$set": {
            "streak": current_streak,
            "last_journal_date":  datetime.combine(today, time.min)
        }}
    )

    save_journal_entry(
        username=username,
        entry_type=req.type,
        prompt=req.prompt,
        response=req.response,
        tags=req.tags,
        mood=req.feeling_now,
        extra_fields=extra_fields
    )

    return {"message": "Detailed journal saved successfully"}



 
# @router.post("/journal/generate-prompt")
# def generate_prompt(req: PromptRequest, token: str = Depends(oauth2_scheme)):
#     valid, username = decode_token(token)
#     if not valid:
#         raise HTTPException(status_code=401, detail=username)

#     prompt = generate_journal_prompt(req.type, req.health_data, req.mood)
#     return {"prompt": prompt}



@router.get("/journal/summary/month")
def get_monthly_summary(token: str = Depends(oauth2_scheme)):
    valid, username = decode_token(token)
    if not valid:
        raise HTTPException(status_code=401, detail=username)

    entries = get_journals_by_user_month(username)
    for entry in entries:
        entry["_id"] = str(entry["_id"])

    responses = [e["response"] for e in entries if e.get("response")]
    summary = summarize_journals(responses)

    return {
        "count": len(responses),
        "summary": summary,
        "entries": entries
    }

@router.get("/journal/by-day")
def get_journals_for_day(
    date: str = Query(..., example="2025-05-20"),
    token: str = Depends(oauth2_scheme)
):
    valid, username = decode_token(token)
    if not valid:
        raise HTTPException(status_code=401, detail=username)

    entries = get_journals_by_day(username, date)
    for entry in entries:
        entry["_id"] = str(entry["_id"])

    return {
        "date": date,
        "count": len(entries),
        "entries": entries
    }


@router.patch("/journal/update")
def patch_journal_entry(req: PatchJournalRequest, token: str = Depends(oauth2_scheme)):
    valid, username = decode_token(token)
    if not valid:
        raise HTTPException(status_code=401, detail=username)

    update_fields = {k: v for k, v in req.dict().items() if k != "journal_id" and v is not None}
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update.")

    patch_journal(req.journal_id, update_fields)

    return {"message": "Journal updated successfully"}