from fastapi import APIRouter, Depends, HTTPException, Body, Query
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import random
import openai  # ✅ Required for GPT

from app.api.v1.auth import decode_token
from app.db.journal_model import save_journal_entry, get_journals_by_user_month, get_journals_by_day, patch_journal
from app.utils.journal_summary_generator import summarize_journals
from app.utils.journal_prompt_generator import generate_journal_prompt

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ✅ Fix: Move fallback outside any class
FALLBACK_QUESTIONS = {
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
        "Thank you. Is there anything else you'd like to add about your day?",
        "Any other thoughts or feelings you'd like to journal?",
        "Would you like to note anything else?",
        "Is there something you wish you’d done differently today?",
        "Anything you'd like to let go of before tomorrow starts?"
    ]
}

# ✅ Fix: Define cache set
recent_journal_prompts = set()

# ✅ Helper: Get morning/afternoon/evening
def get_time_of_day():
    hour = datetime.now().hour
    if hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    else:
        return "evening"

# ✅ GPT-based question generator
# def generate_journal_prompt(category: str, context: str = "", username: str = "", time_of_day: str = ""):
#     attempt = 0
#     max_attempts = 3
#     while attempt < max_attempts:
#         try:
#             system_msg = (
#                 "You're a friendly, compassionate journaling assistant. "
#                 "Follow these rules:\n"
#                 "1. Adjust tone based on time of day (morning/evening).\n"
#                 "2. Tailor to the user's profile/context.\n"
#                 "3. Always be conversational and warm.\n"
#                 "4. If category is 'sleep', end with thank you + ask if user wants to share more.\n"
#                 "5. Avoid repeating exact previous questions.\n"
#                 "6. Always generate one unique, friendly journaling question."
#             )

#             user_msg = f"User: {username}\nTime: {time_of_day}\nCategory: {category}\nContext: {context or 'none'}"

#             response = openai.ChatCompletion.create(
#                 model="gpt-4",
#                 messages=[
#                     {"role": "system", "content": system_msg},
#                     {"role": "user", "content": user_msg}
#                 ],
#                 max_tokens=70,
#                 temperature=0.85
#             )

#             prompt = response['choices'][0]['message']['content'].strip()
#             if prompt not in recent_journal_prompts:
#                 recent_journal_prompts.add(prompt)
#                 if len(recent_journal_prompts) > 100:
#                     recent_journal_prompts.pop()
#                 return prompt
#             else:
#                 attempt += 1  # retry with slight variation
#         except Exception as e:
#             print("⚠️ GPT prompt generation error:", e)
#             attempt += 1

#     raise HTTPException(status_code=500, detail="Failed to generate a unique journaling prompt.")



# ✅ Conversation state store
user_journal_sessions = {}

# ✅ Journal Chat Input
class JournalChatInput(BaseModel):
    user_input: Optional[str] = None

# ✅ Main Journal Conversation Endpoint
@router.post("/journal/conversation")
def journal_conversation(
    body: JournalChatInput,
    token: str = Depends(oauth2_scheme)
):
    valid, username = decode_token(token)
    if not valid:
        raise HTTPException(status_code=401, detail=username)

    user_input = body.user_input or ""
    time_of_day = get_time_of_day()

    if username not in user_journal_sessions:
        questions = [
            generate_journal_prompt("food", username=username, time_of_day=time_of_day),
            generate_journal_prompt("personal", username=username, time_of_day=time_of_day),
            generate_journal_prompt("work_study", username=username, time_of_day=time_of_day),
            generate_journal_prompt("sleep", username=username, time_of_day=time_of_day),
        ]
        user_journal_sessions[username] = {
            "mood": None,
            "answers": [],
            "step": -1,
            "questions": questions,
            "extra_notes": []
        }
        return {
            "question": "👋 Hello! How are you feeling today? Select a mood: 😄 😊 😐 😢 😡 🥱",
            "step": 0
        }

    session = user_journal_sessions[username]
    step = session["step"]

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
            return {
                "question": generate_journal_prompt("extra", username=username, time_of_day=time_of_day),
                "step": session["step"]
            }

    if step >= 4:
        # Append Q&A as "Q: ... A: ..." to extra_notes
        last_question = session.get("last_question", "")
        if user_input and user_input.strip().lower() not in ["no", "nothing", "nope", "i'm good", "na"]:
            session["extra_notes"].append(f"Q: {last_question}\nA: {user_input.strip()}")
        else:
            entry = {
                "food_intake": session["answers"][0],
                "personal": session["answers"][1],
                "work_or_study": session["answers"][2],
                "sleep": session["answers"][3],
                "extra_note": "\n\n".join(session["extra_notes"]),
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

        # Generate next follow-up and save for tracking
        next_question = generate_journal_prompt("extra", username=username, time_of_day=time_of_day)
        session["last_question"] = next_question
        session["step"] += 1
        return {
            "question": next_question,
            "step": session["step"]
        }


# ✅ Patch Journal
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

# ✅ Monthly Summary
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

# ✅ Day Summary
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
