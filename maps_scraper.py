import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("MAPS_KEY")

def get_leads(keyword, locations, min_reviews=3, max_per_city=15, debug=False):
    all_leads = []
    seen = set()

    for location in locations:
        if debug:
            print(f"\n🔍 Searching '{keyword}' in {location}")
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": f"{keyword} near {location}",
            "key": API_KEY
        }

        while True:
            res = requests.get(url, params=params)
            data = res.json()

            for result in data.get("results", []):
                place_id = result["place_id"]

                # Get detailed info
                details_url = "https://maps.googleapis.com/maps/api/place/details/json"
                details_params = {
                    "place_id": place_id,
                    "fields": "name,formatted_address,formatted_phone_number,user_ratings_total,website",
                    "key": API_KEY
                }
                details_res = requests.get(details_url, params=details_params)
                details = details_res.json().get("result", {})

                name = details.get("name")
                phone = details.get("formatted_phone_number")
                address = details.get("formatted_address")
                reviews = details.get("user_ratings_total", 0)
                website = details.get("website")

                if debug:
                    print(f"→ {name} | reviews: {reviews} | phone: {phone}")

                if name and phone and reviews >= min_reviews:
                    key = (name, phone)
                    if key not in seen:
                        seen.add(key)
                        all_leads.append({
                            "name": name,
                            "address": address,
                            "phone": phone,
                            "review_count": reviews,
                            "maps_url": f"https://www.google.com/maps/place/?q=place_id:{place_id}",
                            "city": location,
                            "website": website
                        })
                    if sum(1 for l in all_leads if l["city"] == location) >= max_per_city:
                        break

            if "next_page_token" in data:
                params["pagetoken"] = data["next_page_token"]
                time.sleep(2)
            else:
                break

    return all_leads
