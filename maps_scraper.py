# maps_scraper.py

import os
import time
import requests

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY env var is not set")

# Endpoints
GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
NEARBY_URL   = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
DETAILS_URL  = "https://maps.googleapis.com/maps/api/place/details/json"

def _geocode(city: str) -> tuple[float, float]:
    """Turn a city name into (lat, lng)."""
    resp = requests.get(GEOCODE_URL, params={
        "address": city,
        "key": GOOGLE_API_KEY
    }, timeout=10)
    data = resp.json()
    if data.get("status") != "OK" or not data.get("results"):
        raise ValueError(f"Geocoding failed for {city}: {data.get('status')}")
    loc = data["results"][0]["geometry"]["location"]
    return loc["lat"], loc["lng"]

def _nearby_search(lat: float, lng: float, keyword: str, pagetoken: str | None = None) -> dict:
    """One page of Places Nearby Search."""
    params = {
        "key":     GOOGLE_API_KEY,
        "location": f"{lat},{lng}",
        "radius":   20000,        # 50 km — you can adjust if you like
        "keyword":  keyword,
    }
    if pagetoken:
        params["pagetoken"] = pagetoken
        time.sleep(2)  # required delay before using a next_page_token
    resp = requests.get(NEARBY_URL, params=params, timeout=10)
    return resp.json()

def _place_details(place_id: str) -> dict:
    """Fetch phone, website and formatted_address for one Place."""
    resp = requests.get(DETAILS_URL, params={
        "key":      GOOGLE_API_KEY,
        "place_id": place_id,
        "fields":   "name,formatted_phone_number,website,formatted_address"
    }, timeout=10)
    data = resp.json()
    if data.get("status") != "OK":
        return {}
    return data["result"]

def get_leads(
    niche: str,
    locations: list[str],
    max_pages: int = 5,
    debug: bool = False
) -> list[dict]:
    """
    :param niche: search keyword, e.g. "car detailing"
    :param locations: list of city names, e.g. ["Los Angeles"]
    :param max_pages: how many pages of Nearby Search to fetch (20 results/page)
    :param debug: if True, prints each page's status
    :returns: list of leads with keys 'name','phone','website','address','place_id'
    """
    raw_results = []

    for city in locations:
        # 1) Geocode
        lat, lng = _geocode(city)

        # 2) Nearby Search paging
        pagetoken = None
        for page in range(max_pages):
            data = _nearby_search(lat, lng, niche, pagetoken)
            status = data.get("status")
            if debug:
                print(f"[Nearby][{city}][page {page}] status={status}")
            if status != "OK":
                break
            raw_results.extend(data.get("results", []))
            pagetoken = data.get("next_page_token")
            if not pagetoken:
                break

    # 3) De-duplicate by place_id
    unique = {}
    for r in raw_results:
        pid = r.get("place_id")
        if pid and pid not in unique:
            unique[pid] = r

    # 4) Fetch details for each unique place
    leads = []
    for pid, r in unique.items():
        details = _place_details(pid)
        leads.append({
            "name":    details.get("name", r.get("name","")),
            "phone":   details.get("formatted_phone_number", ""),
            "website": details.get("website", ""),
            "address": details.get("formatted_address", r.get("vicinity","")),
            "place_id": pid,
            # email left blank for your site_scraper fallback
        })

    if debug:
        print(f"► Returning {len(leads)} leads")

    return leads
