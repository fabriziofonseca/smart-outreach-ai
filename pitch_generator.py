# pitch_generator.py

import os
import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

def generate_pitch(lead, calendly_url):
    name = lead["name"]
    city = lead["city"]
    maps_url = lead["maps_url"]
    site_text = lead.get("site_text", "")

    prompt = f"""
You’re a cold-email expert. Return exactly two parts in plain text:

1) A subject line on the first line, exactly:
Subject: Let’s bring more clients to {name}

2) A blank line, then the email body (4–6 sentences).


+ Tone & Structure:
Don't use markdown under any context, use simple plain text. 
+ - Warmly professional — speak to them like a peer, not a robot.
+ - Open with “Hi there,” then immediately reference a specific detail about their business (e.g., recent review, unique service, or something on their homepage).
+ - Clearly state you partner with car detailing businesses to boost appointment volume and automate follow-up.

+ - Use vivid, benefit-driven language (“fill every seat,” “never miss a client,” “watch your revenue rise”) without jargon.



- End with a dual CTA:
  Would you be open to a quick 15-minute call to explore how we can bring in more high-quality leads?  
  You can either reply with a simple “Yes,” and I’ll follow up,  
  or book a time directly here: {calendly_url}

- Sign off exactly:
  Best,  
  Fabrizio Fonseca

Business Details:  
Name: {name}  
City: {city}  
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

    # Split subject and body
    subject_line, body = output.split("\n\n", 1)
    subject = re.sub(r'^[^A-Za-z0-9]+', '', subject_line.replace("Subject:", "")).strip()
    body_text = body.strip()

    return subject, body_text
