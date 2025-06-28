import os
import re
from dotenv import load_dotenv
from openai import OpenAI

from maps_scraper import get_leads
from site_scraper import scrape_site_with_links
from email_sender import send_email

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
You’re a cold-email expert. Output exactly two parts in plain text, nothing else:

1) A single subject line on the very first line, prefixed with "Subject: " and no extra characters. It must read:
Subject: Let’s bring more clients to {name}

2) A blank line, then the 4–7 sentence email body. No markdown, no asterisks, no quotation marks, no bold/italics—just plain text.

Business Details:
Name: {name}
City: {city}
Google Reviews: {reviews}
Google Maps URL: {maps_url}

Website Content:
\"\"\"{site_text.strip()}\"\"\"

Instructions:
- Friendly, professional, benefit-driven tone
- Start “Hi there,” and show you looked them up (mention reviews, service, or site)
- Don’t guess a name—just “Hi there,”
- State you help medspas with lead generation and automations
- Focus on outcomes: more bookings, less manual work, time saved
- End with a variation of this exact line:
With the right systems, you could fill your calendar more consistently and save hours on manual tasks. Would you be open to a quick call to explore how we could make that happen?
- Finish with this signature block (on its own lines):
Best,
Fabrizio Fonseca
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
    # Clean any leading non-alphanumeric characters and extract after "Subject:"
    subject = re.sub(r'^[^A-Za-z0-9]+', '', subject_line.replace("Subject:", "")).strip()
    body_text = body.strip()

    return subject, body_text

if __name__ == "__main__":
    # === Step 1: Get one medspa lead ===
    keyword = "medspa"
    locations = ["Bozeman, MT"]
    leads = get_leads(keyword, locations, min_reviews=3, max_per_city=1, debug=False)

    # === Step 2: Scrape site + generate pitch + send email ===
    for lead in leads:
        if not lead.get("website"):
            print(f"⚠️ No website found for {lead['name']}. Skipping.")
            continue

        print(f"\n🔍 Scraping site for {lead['name']}...\n")
        lead["site_text"] = scrape_site_with_links(
            lead["website"],
            max_pages=5,
            max_chars=3000
        )

        print("🤖 Generating pitch...\n")
        subject, body = generate_pitch(lead)

        print("\n✉️ EMAIL PREVIEW\n")
        print(f"Subject: {subject}\n")
        print(body)

        print("\n📤 Sending to your personal email...\n")
        send_email("fabriziofonsari@gmail.com", subject, body)

        #break  # Only process one for now
