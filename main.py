from maps_scraper import get_leads
from site_scraper import scrape_site_with_links
from pitch_generator import generate_pitch


# Step 1: Get some leads
locations = ["Bozeman, MT"]
keyword = "medspa"
leads = get_leads(keyword, locations, min_reviews=3, max_per_city=3, debug=False)

# Step 2: Scrape homepage + internal links for each lead
for lead in leads:
    print("\n" + "=" * 70)
    print(f"🏢 {lead['name']} ({lead['city']})")
    print(f"📞 {lead['phone']} | ⭐ {lead['review_count']} reviews")
    print(f"📍 {lead['address']}")
    print(f"🗺️  {lead['maps_url']}")
    print(f"🌐 Website: {lead.get('website') or '—'}")

    if lead.get("website"):
        print("\n📄 Full Site Text Preview (homepage + internal pages):\n")
        site_text = scrape_site_with_links(lead["website"], max_pages=5, max_chars=3000)
        print(site_text[:800] + "\n...\n")  # Truncate preview for console
        lead["site_text"] = site_text  # Optionally attach for next steps
    else:
        print("⚠️ No website listed.")

for lead in leads: 
    if "site_text" in lead:
        pitch = generate_pitch(lead)
        print("\n✉️ Pitch:\n")
        print(pitch)
