from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_journal_prompt(entry_type: str, health_data: dict = None, mood: str = None) -> str:
    system_prompt = (
        "You are a caring assistant. Based on the user's health or emotional state, write a short, reflective journaling question."
    )

    user_prompt = f"Generate a journaling question for a {entry_type} entry. "

    if health_data:
        conditions = []
        if health_data.get("spo2", 100) < 90:
            conditions.append("low oxygen levels")
        if health_data.get("heart_rate", 70) > 100 or health_data.get("heart_rate", 70) < 50:
            conditions.append("abnormal heart rate")
        if health_data.get("sleep", 7) < 4:
            conditions.append("insufficient sleep")
        if conditions:
            user_prompt += f"The user's health data shows: {', '.join(conditions)}. "

    if mood:
        user_prompt += f"The user is feeling '{mood}'. "

    user_prompt += "Ask a supportive question to help them reflect."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print("Prompt generation failed:", e)
        return "How are you feeling today?"
