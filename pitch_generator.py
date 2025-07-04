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

def generate_pitch(lead):
    name = lead["name"]
    city = lead["city"]
    maps_url = lead["maps_url"]
    site_text = lead.get("site_text", "")

    prompt = f"""
You’re a cold‐email expert. Return exactly two parts in plain text:

1) A subject line on the first line, exactly:
Subject: Let’s bring more clients to {name}

2) A blank line, then the email body
    Use the two templates below as inspiration but they HAVE to be tailored and personalized on each business. Use the Website Content:
\"\"\"{site_text.strip()}\"\"\" to create a personalized pitch
    You may also pull a specific detail from their site_text to personalize.

---
**TEMPLATE A**
Hey, hope all’s well!  
I came across your business and love how professional and clean your brand looks—exactly the kind of shop our system works best for.  
We’ve built something called SmartBooking designed specifically for detailers who want to book more high-paying jobs like ceramic coatings, PPF, and full details without dealing with lowballers or no-shows.  
Some of the guys we work with are now adding $8–$12K/month on autopilot. We handle the marketing and lead filtering so you can just focus on your craft.  
No results? You don’t pay. Simple as that.  
We’re being selective and opening just 3 slots, being honest {name} looks like a great contender.

**TEMPLATE B**
Hey {name}, I hope you’re doing great today,  
Love how clean and professional {name} looks and so I'm reaching out with something that will make a difference…  
Over the past few months, we’ve developed a system called SmartBooking, designed specifically for car detailers who want to attract better customers—people who don’t haggle on price, value quality, and are ready to book services like PPF, ceramic coatings, or full details.  
If you’ve got room for such jobs, my team and I can help by streamlining everything so you can focus on detailing while we bring in the right clients and keep your schedule packed.  
Right now, we’re looking to work with just 3 more detailers—based on what I’ve seen, you seem like the best fit.  
The best part is… if we don’t deliver, you don’t pay! We work on a guarantee basis so if you see no results, we don’t get paid.  
Rather than making this a novel, let’s hop on a quick 5–20 minute call. If it’s not a good fit, I’ll pay you for an hour of your time.

---
End with this CTA (exactly as written):
Would you be open to a quick 15-minute call to explore how we can bring in more high-quality leads?
You can either reply with a simple “Yes,” and I’ll follow up,

Thanks,
Emanuel
--
Emanuel Wetter / Co-Owner
C: CoCreate
P: (312)-847-2902
A: 1075 W Roosevelt Rd, Chicago, IL

Business Details:
Name: {name}
City: {city}
Google Maps URL: {maps_url}

Website Content:
\"\"\"{site_text.strip()}\"\"\"
"""
    return prompt


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
