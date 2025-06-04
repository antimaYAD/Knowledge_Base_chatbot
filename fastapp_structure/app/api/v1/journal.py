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

# class RichJournalEntry(BaseModel):
#     type: str  # "triggered" or "scheduled"
#     prompt: str
#     response: str
#     feeling_now: str
#     feeling_most_of_day: Union[str, List[str]]
#     triggered_by: Union[str, List[str]]
#     expressed_to: Union[str, List[str]]
#     body_reaction: Union[str, List[str]]
#     note: Optional[str] = None
#     tags: Optional[List[str]] = []



# class PromptRequest(BaseModel):
#     type: str  # "triggered" or "scheduled"
#     mood: Optional[str] = None
#     health_data: Optional[dict] = None  # keys: spo2, heart_rate, sleep


# class PatchJournalRequest(BaseModel):
#     journal_id: str
#     response: Optional[str] = None
#     feeling_now: Optional[str] = None
#     feeling_most_of_day: Optional[Union[str, List[str]]] = None
#     triggered_by: Optional[Union[str, List[str]]] = None
#     expressed_to: Optional[Union[str, List[str]]] = None
#     body_reaction: Optional[Union[str, List[str]]] = None
#     note: Optional[str] = None
#     tags: Optional[List[str]] = None


    

# @router.post("/journal/save-detailed")
# def save_rich_journal(req: RichJournalEntry, token: str = Depends(oauth2_scheme)):
#     valid, username = decode_token(token)
#     if not valid:
#         raise HTTPException(status_code=401, detail=username)

#     extra_fields = {
#         "feeling_now": req.feeling_now,
#         "feeling_most_of_day": req.feeling_most_of_day,
#         "triggered_by": req.triggered_by,
#         "expressed_to": req.expressed_to,
#         "body_reaction": req.body_reaction,
#         "note": req.note
#     }

#     today = datetime.utcnow().date()
#     user = users_collection.find_one({"username": username})
#     last_date = user.get("last_journal_date")
#     current_streak = user.get("streak", 0)

#     if last_date == today:
#         pass  # Already journaled today
#     elif last_date == today - timedelta(days=1):
#         current_streak += 1
#     else:
#         current_streak = 1  # Reset

#     users_collection.update_one(
#         {"username": username},
#         {"$set": {
#             "streak": current_streak,
#             "last_journal_date":  datetime.combine(today, time.min)
#         }}
#     )

#     save_journal_entry(
#         username=username,
#         entry_type=req.type,
#         prompt=req.prompt,
#         response=req.response,
#         tags=req.tags,
#         mood=req.feeling_now,
#         extra_fields=extra_fields
#     )

#     return {"message": "Detailed journal saved successfully"}



 
# # @router.post("/journal/generate-prompt")
# # def generate_prompt(req: PromptRequest, token: str = Depends(oauth2_scheme)):
# #     valid, username = decode_token(token)
# #     if not valid:
# #         raise HTTPException(status_code=401, detail=username)

# #     prompt = generate_journal_prompt(req.type, req.health_data, req.mood)
# #     return {"prompt": prompt}



# @router.get("/journal/summary/month")
# def get_monthly_summary(token: str = Depends(oauth2_scheme)):
#     valid, username = decode_token(token)
#     if not valid:
#         raise HTTPException(status_code=401, detail=username)

#     entries = get_journals_by_user_month(username)
#     for entry in entries:
#         entry["_id"] = str(entry["_id"])

#     responses = [e["response"] for e in entries if e.get("response")]
#     summary = summarize_journals(responses)

#     return {
#         "count": len(responses),
#         "summary": summary,
#         "entries": entries
#     }

# @router.get("/journal/by-day")
# def get_journals_for_day(
#     date: str = Query(..., example="2025-05-20"),
#     token: str = Depends(oauth2_scheme)
# ):
#     valid, username = decode_token(token)
#     if not valid:
#         raise HTTPException(status_code=401, detail=username)

#     entries = get_journals_by_day(username, date)
#     for entry in entries:
#         entry["_id"] = str(entry["_id"])

#     return {
#         "date": date,
#         "count": len(entries),
#         "entries": entries
#     }


# @router.patch("/journal/update")
# def patch_journal_entry(req: PatchJournalRequest, token: str = Depends(oauth2_scheme)):
#     valid, username = decode_token(token)
#     if not valid:
#         raise HTTPException(status_code=401, detail=username)

#     update_fields = {k: v for k, v in req.dict().items() if k != "journal_id" and v is not None}
#     if not update_fields:
#         raise HTTPException(status_code=400, detail="No fields to update.")

#     patch_journal(req.journal_id, update_fields)

#     return {"message": "Journal updated successfully"}

####version 2

import random
from fastapi import Body

from pydantic import BaseModel

import random
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.security import OAuth2PasswordBearer
from app.db.database import users_collection
from app.api.v1.auth import decode_token
from app.db.journal_model import save_journal_entry

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class JournalChatInput(BaseModel):
    user_input: Optional[str] =None

QUESTION_POOLS = {
    "food": [
        "What did you eat today?",
        "Did you try anything new for your meals today?",
        "How did you feel about your food choices today?"
    ],
    "personal": [
        "Did you do anything for your wellbeing today?",
        "How did you take care of yourself today?",
        "Was there a moment you felt proud of yourself today?"
    ],
    "work_study": [
        "How was your work or study today?",
        "Did you accomplish something at work or school?",
        "What was the most interesting part of your work/study today?"
    ],
    "sleep": [
        "How did you sleep last night?",
        "Did you feel rested when you woke up?",
        "Was your sleep different from usual?"
    ],
    "extra": [
        "Thank you, Is there anything else you'd like to add about your day?",
        "Thank you, Any other thoughts or feelings you'd like to journal?",
        "Thank you, Would you like to note anything else?",
        "Thank you, Is there something you wish you’d done differently today?",
        "Thank you, Anything you'd like to let go of before tomorrow starts?"
    ]
}

user_journal_sessions = {}

@router.post("/journal/conversation")
def journal_conversation(token: str = Depends(oauth2_scheme), user_input: str = Body(default=None, embed=True)):
    valid, username = decode_token(token)
    


    if not valid:
        raise HTTPException(status_code=401, detail=username)

    user_input = user_input or ""

    if username not in user_journal_sessions:
        questions = [
            random.choice(QUESTION_POOLS["food"]),
            random.choice(QUESTION_POOLS["personal"]),
            random.choice(QUESTION_POOLS["work_study"]),
            random.choice(QUESTION_POOLS["sleep"]),
        ]
        user_journal_sessions[username] = {
            "mood": None,
            "answers": [],
            "step": -1,  # -1 = ask mood first
            "questions": questions,
            "extra_notes": []
        }
        return {"question": "👋 Hello! How are you feeling today? Select a mood: 😄 😊 😐 😢 😡 🥱", "step": 0}

    session = user_journal_sessions[username]
    step = session["step"]

    # Step -1: Mood collection
    if step == -1:
        session["mood"] = user_input.strip() or "😐"
        session["step"] = 0
        return {"question": session["questions"][0], "step": 1}
    
    if step < 4:
        if user_input:
            session["answers"].append(user_input)
        session["step"] += 1
        if session["step"] < 4:
            return {"question": session["questions"][session["step"]], "step": session["step"] + 1}
        else:
            # Just completed the last main question, move to extra loop
            return {"question": random.choice(QUESTION_POOLS["extra"]), "step": session["step"]}


    # if step < 4 and user_input:
    #     session["answers"].append(user_input)
    #     session["step"] += 1
    #     if session["step"] < 4:
    #         return {"question": session["questions"][session["step"]], "step": session["step"] + 1}

    # Extra note loop
    if step >= 4:
        if user_input and user_input.strip().lower() not in ["no", "nothing", "nope", "i'm good", "na"]:
            session["extra_notes"].append(user_input)
        elif user_input and user_input.strip().lower() in ["no", "nothing", "nope", "i'm good", "na"]:
            entry = {
                "food_intake": session["answers"][0] if len(session["answers"]) > 0 else "",
                "personal": session["answers"][1] if len(session["answers"]) > 1 else "",
                "work_or_study": session["answers"][2] if len(session["answers"]) > 2 else "",
                "sleep": session["answers"][3] if len(session["answers"]) > 3 else "",
                "extra_note": " ".join(session["extra_notes"]),
            }
            save_journal_entry(
                username=username,
                entry_type="conversation",
                prompt="Conversational Journal",
                response=str(entry),
                tags=[],
                mood=session["mood"],
                extra_fields=entry
            )
            user_journal_sessions.pop(username, None)
            return {"message": "✅ Thank you for journaling today! Your notes have been saved."}

        session["step"] += 1
        return {"question": random.choice(QUESTION_POOLS["extra"]), "step": session["step"]}



class PatchConversationJournalRequest(BaseModel):
    journal_id: str
    food_intake: str = None
    personal: str = None
    work_or_study: str = None
    sleep: str = None
    extra_note: str = None

@router.patch("/journal/conversation")
def patch_conversation_journal(req: PatchConversationJournalRequest, token: str = Depends(oauth2_scheme)):
    valid, username = decode_token(token)
    if not valid:
        raise HTTPException(status_code=401, detail=username)

    update_fields = {k: v for k, v in req.dict().items() if k != "journal_id" and v is not None}
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update.")

    patch_journal(req.journal_id, update_fields)
    return {"message": "Conversational journal updated successfully"}


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
