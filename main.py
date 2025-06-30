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

# Initialize session state storages
if 'export_df' not in st.session_state:
    st.session_state.export_df = None
if 'send_leads' not in st.session_state:
    st.session_state.send_leads = []

# Page config and sidebar
st.set_page_config(page_title="Smart Outreach AI", layout="centered")
st.sidebar.title("🛠️ Settings")
calendly_url  = st.sidebar.text_input("Your Calendly link", value=st.session_state.get("calendly_url", ""))
sender_email = st.sidebar.text_input("Your Gmail address",    value=st.session_state.get("sender_email", ""))
app_password = st.sidebar.text_input("Your Gmail App Password", type="password", value=st.session_state.get("app_password", ""))
lead_limit   = st.sidebar.slider("Max # of leads", 0, 50, 10, help="How many leads to fetch/scrape at once")

if calendly_url:  st.session_state.calendly_url   = calendly_url
if sender_email: st.session_state.sender_email  = sender_email
if app_password: st.session_state.app_password  = app_password

# Map selector
with st.expander("📍 Choose target location", expanded=True):
    map_obj  = folium.Map(location=[39.8283, -98.5795], zoom_start=4, control_scale=True)
    map_data = st_folium(map_obj, height=500, width=800, returned_objects=["center"])
    if st.button("✅ Use This Location"):
        center = map_data.get("center")
        if center:
            st.session_state.map_center = center
            st.success(f"Selected: {center['lat']:.4f}, {center['lng']:.4f}")
        else:
            st.warning("Wait for the map to load before selecting.")

# Reverse geocode to city
geolocator = Nominatim(user_agent="smart-outreach-ai")
coords     = st.session_state.get("map_center")
city       = ""
if coords:
    try:
        loc  = geolocator.reverse((coords['lat'], coords['lng']), timeout=10)
        addr = loc.raw.get("address", {})
        city = addr.get("city") or addr.get("town") or addr.get("village") or ""
        if city:
            st.success(f"City: {city} ({coords['lat']:.4f}, {coords['lng']:.4f})")
        else:
            st.warning("No city found at these coordinates.")
    except Exception as e:
        st.error("Failed to reverse geocode.")
        st.text(str(e))
else:
    st.info("Select a city via the map above.")

# Niche input
niche = st.text_input("Niche")

# Fetch & store leads for CSV export
if st.button("📤 Fetch Leads for Export"):
    if not city:
        st.warning("Pick a city first.")
    else:
        raw = get_leads(niche, [city], min_reviews=3, debug=False)[:lead_limit]
        rows = []
        for lead in raw:
            email = lead.get("email", "") or ""
            if not email and lead.get("website"):
                found = scrape_emails(lead["website"], max_pages=5)
                email = found[0] if found else ""
            rows.append({
                "Business Name": lead.get("name", ""),
                "Phone":          lead.get("phone", ""),
                "Email":          email,
                "Website":        lead.get("website", ""),
                "Location":       lead.get("address", "")
            })
        df = pd.DataFrame(rows)
        st.session_state.export_df = df
        st.success(f"Fetched {len(df)} leads.")

# Always show Download button if data exists
if st.session_state.export_df is not None:
    csv_bytes = st.session_state.export_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Leads CSV",
        data=csv_bytes,
        file_name="leads.csv",
        mime="text/csv",
        key="download_leads"
    )

# Load leads into session for emailing
if st.button("📧 Load Leads for Emailing"):
    if not calendly_url or not city or not app_password:
        st.warning("Please make sure that Canledly Link, City and Gmail Password are completed")
    else:
        leads = get_leads(niche, [city], min_reviews=3, debug=False)[:lead_limit]
        # attach sent flag
        for ld in leads:
            ld.setdefault("sent", False)
        st.session_state.send_leads = leads
        st.success(f"Loaded {len(leads)} leads for emailing.")

# Iterate over stored leads for send/pitch UI
for idx, lead in enumerate(st.session_state.send_leads):
    st.divider()
    st.subheader(lead.get("name", ""))
    st.write(f"📍 {lead.get('address','')}  \n📞 {lead.get('phone','')}  \n⭐ {lead.get('review_count',0)} reviews")

    # Extract or scrape email if not already present
    email = lead.get("email", "") or ""
    if not email and lead.get("website"):
        found = scrape_emails(lead["website"], max_pages=5)
        email = found[0] if found else ""
    st.write(f"✉️ Found email: **{email or 'none'}**")

    # Generate pitch once
    if not lead.get("pitched", False):
        subject, body = generate_pitch(lead, calendly_url)
        lead["_subject"] = subject
        lead["_body"]    = body
        lead["pitched"]  = True
    else:
        subject = lead.get("_subject", "")
        body    = lead.get("_body", "")

    st.code(f"Subject: {subject}")
    st.text_area("Email Body", value=body, height=200, key=f"body_{idx}")

    if email:
        if not lead.get("sent"):
            if st.button("Send Email", key=f"send_{idx}"):
                send_email(
                    to_email=email,
                    subject=subject,
                    body=body,
                    from_email=sender_email,
                    email_password=app_password
                )
                lead["sent"] = True
                st.success(f"Sent to {email}!")
        else:
            st.info(f"✅ Email already sent to {email}.")
    else:
        st.warning("No email to send to for this lead.")


# After all leads UI
if st.session_state.send_leads:
    st.success(f"🚀 Lead generation complete! {len(st.session_state.send_leads)} leads loaded.")

# Email generation complete message
if st.session_state.send_leads and all(lead.get('pitched', False) for lead in st.session_state.send_leads):
    st.success("✉️ All email pitches generated and ready for review!")