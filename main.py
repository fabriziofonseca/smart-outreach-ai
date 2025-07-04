# main.py
import streamlit as st
from maps_scraper import get_leads
from site_scraper import  scrape_emails
from pitch_generator import generate_pitch
from email_sender import send_email
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

# --- Page Setup ---
st.set_page_config(page_title="Smart Outreach AI", layout="centered")
st.title("Smart Outreach AI")

# --- Sidebar Settings ---
st.sidebar.header("Settings")
#calendly_url = st.sidebar.text_input("Your Calendly link", value=st.session_state.get("calendly_url", ""))
sender_email = st.sidebar.text_input("Your Gmail address", value=st.session_state.get("sender_email", ""))
app_password = st.sidebar.text_input("Your App Password", type="password", value=st.session_state.get("app_password", ""))
max_pages = st.sidebar.slider("Max API pages", 1, 5, st.session_state.get("max_pages", 3))
lead_limit = st.sidebar.slider("Max # of leads to process", 0, 100, st.session_state.get("lead_limit", 50))

# Persist sidebar inputs
# for key, val in {"calendly_url": calendly_url, "sender_email": sender_email, "app_password": app_password,
for key, val in { "sender_email": sender_email, "app_password": app_password,
                 "max_pages": max_pages, "lead_limit": lead_limit}.items():
    if val is not None:
        st.session_state[key] = val

# --- Map Selector ---
st.subheader("📍 Choose Target Location")
with st.expander("Click to pick on map", expanded=True):
    m = folium.Map(location=[39.8283, -98.5795], zoom_start=4)
    md = st_folium(m, height=400, width=700, returned_objects=["center"])
    if st.button("Use This Location"):
        center = md.get("center")
        if center:
            st.session_state.map_center = center
        else:
            st.warning("Wait for map to load before clicking.")

# --- Reverse Geocode to City ---
st.subheader("Selected City")
coords = st.session_state.get("map_center")
city = ""
if coords:
    try:
        loc = Nominatim(user_agent="smart-outreach-ai").reverse((coords['lat'], coords['lng']), timeout=10)
        addr = loc.raw.get('address', {})
        city = addr.get('city') or addr.get('town') or addr.get('village') or ''
        if city:
            st.success(f"{city} ({coords['lat']:.4f}, {coords['lng']:.4f})")
    except Exception:
        st.error("Could not reverse geocode coordinates.")
else:
    st.info("Select a location on the map above.")

# --- Niche Input ---
st.subheader("Niche")
niche = st.text_input("Enter your niche (e.g., 'coffee shop')")

# --- Session State ---
if 'export_df' not in st.session_state:
    st.session_state.export_df = None
if 'send_leads' not in st.session_state:
    st.session_state.send_leads = []

# --- Fetch & Export Leads ---
st.subheader("Fetch Leads for Export")
if st.button("Fetch & Export Leads"):
    if not niche or not city:
        st.warning("Select a location and enter a niche first.")
    else:
        try:
            leads = get_leads(niche, [city], max_pages=st.session_state.max_pages, debug=True)
        except ValueError as e:
            st.error(f"API Error: {e}")
            leads = []
        leads = leads[:st.session_state.lead_limit]
       # st.write(f"🔍 Raw leads fetched: {len(leads)}")
        rows = []
        for lead in leads:
            email = lead.get('email') or ''
            if not email and lead.get('website'):
                found = scrape_emails(lead['website'], max_pages=5)
                email = found[0] if found else ''
            rows.append({
                'name': lead.get('name',''),
                'phone': lead.get('phone',''),
                'email': email,
                'website': lead.get('website',''),
                'address': lead.get('address',''),
                'city':city,
                'maps_url': f"https://www.google.com/maps/place/?q=place_id:{lead.get('place_id','')}"
            })
        df = pd.DataFrame(rows)
        st.session_state.export_df = df
        st.success(f"🚀 Fetched {len(df)} leads. Download below.")

# --- Download CSV ---
if st.session_state.export_df is not None:
    st.download_button("Download Leads CSV",
                       data=st.session_state.export_df.to_csv(index=False).encode('utf-8'),
                       file_name="leads.csv",
                       mime="text/csv")

# --- Generate & Send Emails (locked until creds are entered) ---
#if not calendly_url or not sender_email or not app_password:
if not sender_email or not app_password:
    st.warning("🔒 Enter your Gmail address and App Password above to enable email generation.")
else:
    # --- Load Leads for Emailing ---
    st.subheader("Generate & Send Emails")
    if st.button("Load Leads for Emailing"):
        if st.session_state.export_df is None:
            st.warning("Fetch leads first above.")
        else:
            st.session_state.send_leads = st.session_state.export_df.to_dict('records')
            for lead in st.session_state.send_leads:
                lead['sent'] = False
                lead['pitched'] = False
            st.success(f"🔄 Loaded {len(st.session_state.send_leads)} leads for emailing.")

    # --- Email Pitch & Send Loop ---
    for idx, lead in enumerate(st.session_state.send_leads):
        st.divider()
        email = lead.get('email','')

        if not email:
            st.warning(f"Skipping this lead - No email address")
            continue

        # Only generate for leads that haven’t been pitched yet
        if not lead['pitched']:
            #subj, body = generate_pitch(lead, calendly_url)
            subj, body = generate_pitch(lead)
            lead['_subj'], lead['_body'], lead['pitched'] = subj, body, True

        st.write(f"### {lead.get('name')}")
        st.write(f"✉️ {email}")
        st.code(f"Subject: {lead['_subj']}")
        st.text_area("Body", value=lead['_body'], height=200, key=f"body_{idx}")

        if not lead['sent']:
            if not email:
                st.warning(f"Cannot send email because there's no email address")
            elif st.button("Send Emai", key=f"send_{idx}"):
                send_email(
                    to_email=email,
                    subject=lead['_subj'],
                    body=lead['_body'],
                    from_email=sender_email,
                    email_password=app_password
                )
                lead['sent'] = True
                st.success(f"✅ Email sent to {email}")
