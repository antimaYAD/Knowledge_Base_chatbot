from datetime import datetime
from app.db.journal_model import save_journal_entry
from app.utils.journal_prompt_generator import generate_journal_prompt
from app.db.database import get_all_users_and_times  # ensure this returns list of dicts
from apscheduler.schedulers.background import BackgroundScheduler

def check_journal_times():
    now = datetime.now().strftime("%H:%M")
    users = get_all_users_and_times()  # should return list of { username, journal_time }

    for user in users:
        journal_time = user.get("journal_time")
        username = user.get("username")

        if not username or not journal_time:
            continue

        if journal_time == now:
            try:
                prompt = generate_journal_prompt("scheduled", username=username, time_of_day=get_time_of_day())
            except Exception as e:
                print(f"⚠️ Failed to generate prompt for {username}: {e}")
                prompt = f"How are you feeling this {get_time_of_day()}?"

            save_journal_entry(
                username=username,
                entry_type="scheduled",
                prompt=prompt,
                response="",
                tags=["auto-scheduled"],
                mood="neutral"
            )
            print(f"✅ Journal prompt scheduled for {username} at {now}")

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_journal_times, trigger="interval", minutes=1, id="check_journal_times", misfire_grace_time=60)
    scheduler.start()
