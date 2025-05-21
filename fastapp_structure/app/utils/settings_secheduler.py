from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from app.db.database import get_all_users_and_times
from app.db.journal_model import save_journal_entry
from app.utils.journal_prompt_generator import generate_journal_prompt

scheduler = BackgroundScheduler()

def check_journal_times():
    now = datetime.now().strftime("%H:%M")
    users = get_all_users_and_times()

    for user in users:
        if user.get("journal_time") == now:
            prompt = generate_journal_prompt("scheduled", mood="neutral")
            save_journal_entry(
                username=user["username"],
                entry_type="scheduled",
                prompt=prompt,
                response="",
                tags=["auto-scheduled"],
                mood="neutral"
            )

def start_scheduler():
    scheduler.add_job(check_journal_times, trigger="interval", minutes=1)
    scheduler.start()
