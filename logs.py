# logs.py
import streamlit as st
import googlemaps
from datetime import datetime
from db import get_client

# Cliente de Google Maps, inicializado con la clave del secrets
gmaps = googlemaps.Client(key=st.secrets["googlemaps"]["google_maps_api_key"])

def get_log_collection():
    client = get_client()
    db = client[st.secrets["mongodb"]["db"]]
    return db["access_logs"]  # colección para logs de accesos

def get_coordinates(address):
    try:
        geocode_result = gmaps.geocode(address)
        if geocode_result:
            location = geocode_result[0]["geometry"]["location"]
            return location["lat"], location["lng"]
    except Exception as e:
        print(f"Error al geocodificar dirección: {e}")
    return None, None

def log_access(address=None):
    col = get_log_collection()
    lat, lon = None, None
    if address:
        lat, lon = get_coordinates(address)
    doc = {
        "evento": "acceso_app",
        "fecha": datetime.now(),
        "latitud": lat,
        "longitud": lon,
        "direccion": address,
    }
    col.insert_one(doc)

def get_access_logs(limit=20):
    col = get_log_collection()
    cursor = col.find({"evento": "acceso_app"}).sort("fecha", -1).limit(limit)
    return list(cursor)
