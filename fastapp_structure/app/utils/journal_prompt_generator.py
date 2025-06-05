from openai import OpenAI
import os
from fastapi import HTTPException
from datetime import datetime

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 🔥 Add this to track duplicates
recent_journal_prompts = set()

def generate_journal_prompt(category: str, context: str = "", username: str = "", time_of_day: str = ""):
    attempt = 0
    max_attempts = 3
    while attempt < max_attempts:
        try:
            system_msg = (
                "You are a journaling assistant.\n"
                "Follow these rules:\n"
                "1. Do NOT greet the user in the question (no 'Hello', 'Hi', etc).\n"
                "2. Ask short, focused journaling questions.\n"
                "3. Match the tone to time of day (optional).\n"
                "4. If category is 'sleep', end with a gentle closing prompt.\n"
                "5. Avoid repeating earlier questions.\n"
                "6. Keep it conversational but concise (1 sentence)."
            )

            user_msg = f"User: {username}\nTime: {time_of_day}\nCategory: {category}\nContext: {context or 'none'}"

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                max_tokens=70,
                temperature=0.85
            )

            prompt = response.choices[0].message.content.strip()  # ✅ Correct usage
            if prompt not in recent_journal_prompts:
                recent_journal_prompts.add(prompt)
                if len(recent_journal_prompts) > 100:
                    recent_journal_prompts.pop()
                return prompt
            else:
                attempt += 1
        except Exception as e:
            print("⚠️ GPT prompt generation error:", e)
            attempt += 1

    raise HTTPException(status_code=500, detail="Failed to generate a unique journaling prompt.")
