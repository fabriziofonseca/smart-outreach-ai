import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

def generate_pitch(lead):
    name = lead["name"]
    city = lead["city"]
    reviews = lead["review_count"]
    maps_url = lead["maps_url"]
    site_text = lead.get("site_text", "")

    prompt = f"""
You’re a cold-email expert. Return exactly two parts in plain text:

1) A subject line on the first line, exactly:
Subject: Let’s bring more clients to {name}

2) A blank line, then the email body (4–6 sentences).

Tone & Structure:
- Professional and concise.
- Begin “Hi there,” and note their review count (e.g., “I saw you have 82 Google reviews—great work!”).
- State you help medspas with lead generation and automations.
- Highlight concrete benefits: more consistent bookings, less manual follow-up.
- End with a clear, polite CTA:  
  Would you be open to a brief call to discuss?  
- Sign off exactly:  
  Best,  
  Fabrizio Fonseca

Business Details:  
Name: {name}  
City: {city}  
Reviews: {reviews}  
Google Maps URL: {maps_url}

Website Content:  
\"\"\"{site_text.strip()}\"\"\"
"""
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=300
    )

    output = response.choices[0].message.content.strip()
    lines = output.split("\n", 1)
    subject = lines[0].replace("Subject:", "").strip()
    body = lines[1].strip() if len(lines) > 1 else ""

    return subject.strip(), body.strip()
