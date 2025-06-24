import os
from dotenv import load_dotenv
import openai

load_dotenv()
openai.api_key = os.getenv("DEEPSEEK_API_KEY")

def generate_pitch(lead):
    name = lead["name"]
    city = lead["city"]
    reviews = lead["review_count"]
    maps_url = lead["maps_url"]
    site_text = lead.get("site_text", "")

    prompt = f"""
You're a cold email expert. Write a short personalized cold email to the owner of a medspa based on the following business info.

Business Name: {name}
City: {city}
Review Count: {reviews}
Google Maps: {maps_url}

Website Content:
\"\"\"
{site_text.strip()}
\"\"\"

Your task:
- Write in a friendly, casual tone
- Reference something from their website content or services if possible
- Mention that you help medspas with lead generation + automations
- End with a soft call to action for a quick chat

Limit to 3–5 sentences.
"""

    response = openai.ChatCompletion.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=300
    )

    return response["choices"][0]["message"]["content"].strip()
