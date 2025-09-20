# logs.py
import streamlit as st
from datetime import datetime
from db import get_client

@st.cache_resource
def get_log_collection():
    client = get_client()
    db = client[st.secrets["mongodb"]["db"]]
    return db["access_logs"]

def log_access(lat=None, lon=None):
    col = get_log_collection()
    doc = {
        "evento": "acceso_app",
        "fecha": datetime.now(),
        "latitud": lat,
        "longitud": lon,
    }
    col.insert_one(doc)

def get_access_logs(limit=20):
    col = get_log_collection()
    cursor = col.find({"evento": "acceso_app"}).sort("fecha", -1).limit(limit)
    return list(cursor)
