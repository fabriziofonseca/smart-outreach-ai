# main.py
import streamlit as st
from maps_scraper import get_leads
from site_scraper import scrape_site_with_links, scrape_emails
from pitch_generator import generate_pitch
from email_sender import send_email
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

# Setup
st.set_page_config(page_title="Smart Outreach AI", layout="centered")

# Sidebar settings
st.sidebar.title("🛠️ Settings")
calendly_url  = st.sidebar.text_input("Your Calendly link", value=st.session_state.get("calendly_url", ""))
sender_email = st.sidebar.text_input("Your Gmail address", value=st.session_state.get("sender_email", ""))
app_password = st.sidebar.text_input("Your Gmail App Password", type="password", value=st.session_state.get("app_password", ""))

if calendly_url:  st.session_state.calendly_url   = calendly_url
if sender_email: st.session_state.sender_email  = sender_email
if app_password: st.session_state.app_password  = app_password

# Map UI
with st.expander("📍 Click on the map to choose a target location", expanded=True):
    default_location = [39.8283, -98.5795]
    map_object = folium.Map(location=default_location, zoom_start=4, control_scale=True)
    map_data   = st_folium(map_object, height=500, width=800, returned_objects=["center"])

    if st.button("✅ Use This Location"):
        center = map_data.get("center")
        if center:
            st.session_state.map_center = center
            st.success(f"Selected location: {center['lat']:.4f}, {center['lng']:.4f}")
        else:
            st.warning("Please wait for the map to load before selecting a location.")

# Reverse geocode
geolocator = Nominatim(user_agent="smart-outreach-ai")
city       = ""
coords     = st.session_state.get("map_center")
if coords:
    try:
        loc = geolocator.reverse((coords['lat'], coords['lng']), timeout=10)
        addr = loc.raw.get("address", {})
        city = addr.get("city") or addr.get("town") or addr.get("village") or ""
        if city:
            st.success(f"Selected location: {city} ({coords['lat']:.4f}, {coords['lng']:.4f})")
        else:
            st.warning("Coordinates selected, but no city name found.")
    except Exception as e:
        st.error("⚠️ Failed to detect city from coordinates. Try again.")
        st.text(f"Error: {e}")
else:
    st.info("Click on the map to choose a target location.")

# Niche input
niche = st.text_input("Niche")

# Export Leads
if st.button("📤 Fetch & Export Leads"):
    if not city:
        st.warning("Select a city on the map first.")
    else:
        raw_leads = get_leads(niche, [city], min_reviews=3, debug=False)
        export_data = []

        for lead in raw_leads:
            email = lead.get("email", "") or ""
            # fallback: scrape site for email
            if not email and lead.get("website"):
                found = scrape_emails(lead["website"], max_pages=5)
                email = found[0] if found else ""

            export_data.append({
                "Business Name": lead.get("name", ""),
                "Phone"       : lead.get("phone", ""),
                "Email"       : email,
                "Website"     : lead.get("website", ""),
                "Location"    : lead.get("address", "")
            })

        df  = pd.DataFrame(export_data)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Leads CSV", csv, "leads.csv", "text/csv")

# Generate Email
if st.button("Generate Email"):
    if not calendly_url:
        st.warning("Please enter your Calendly link.")
    elif not city:
        st.warning("Select a city from the map first.")
    else:
        leads = get_leads(niche, [city], min_reviews=3, debug=False)
        for lead in leads:
            if not lead.get("website"):
                st.error(f"No website for {lead['name']}. Skipping.")
                continue

            st.subheader(lead['name'])
            st.write(f"📍 {lead['address']}  \n📞 {lead['phone']}  \n⭐ {lead['review_count']} reviews")

            # get site text for pitch
            site_text = scrape_site_with_links(lead['website'], max_pages=5, max_chars=3000)
            lead['site_text'] = site_text

            # extract email from site
            found = scrape_emails(lead['website'], max_pages=5)
            lead_email = found[0] if found else ""
            st.write(f"✉️  Found email: **{lead_email or 'none'}**")
            st.session_state.lead_email = lead_email

            # generate pitch
            subject, body = generate_pitch(lead, calendly_url)
            st.session_state.email_subject = subject
            st.session_state.email_body    = body
            st.session_state.email_ready   = True
            st.session_state.lead_name     = lead['name']

            st.code(f"Subject: {subject}", language="text")
            st.text_area("Email Body", value=body, height=200)
            break

# Send Email
if st.session_state.get('email_ready', False):
    if st.button("Send Email to Lead", key=f"send_{st.session_state.lead_name}"):
        to_addr = st.session_state.lead_email
        if not to_addr:
            st.warning("No recipient email found. Cannot send.")
        elif not sender_email or not app_password:
            st.warning("Your Gmail + App Password are required.")
        else:
            send_email(
                to_email=      to_addr,
                subject=       st.session_state.email_subject,
                body=          st.session_state.email_body,
                from_email=    sender_email,
                email_password=app_password
            )
            st.success(f"✅ Email sent to {to_addr}!")