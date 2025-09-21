# location.py
import requests
import streamlit as st

def get_location_google():
    """
    Usa la API de Google Maps Geolocation para obtener lat/lon actuales.
    Retorna (lat: float, lon: float, accuracy: float | None).
    """
    api_key = st.secrets["googlemaps"]["google_maps_api_key"]
    url = f"https://www.googleapis.com/geolocation/v1/geolocate?key={api_key}"

    try:
        r = requests.post(url, json={})
        if r.status_code == 200:
            data = r.json()
            lat = data["location"]["lat"]
            lon = data["location"]["lng"]
            accuracy = data.get("accuracy")
            return float(lat), float(lon), accuracy
        else:
            st.error(f"Google API error {r.status_code}: {r.text}")
    except Exception as e:
        st.error(f"Error consultando Google API: {e}")

    return None, None, None
