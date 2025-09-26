# main.py
import streamlit as st
import pytz
from db import get_latest_record, get_access_logs
from geolocation import handle_geolocation
from photo_checker import check_and_update_photo
from sections import render_inspector, render_controls, render_history

st.set_page_config(page_title="📸 Update", layout="centered")
colombia = pytz.timezone("America/Bogota")

if "geo_data" not in st.session_state:
    st.session_state.geo_data = None

st.title("📸 Update")

handle_geolocation(st.session_state)
latest = get_latest_record()

render_inspector(latest, st.session_state.geo_data)
render_controls(latest, st.session_state.geo_data, check_and_update_photo)
render_history(get_access_logs(), colombia)
