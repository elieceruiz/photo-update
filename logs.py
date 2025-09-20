# logs.py
import streamlit as st
from datetime import datetime
from pymongo import MongoClient
import pytz

colombia_tz = pytz.timezone("America/Bogota")

@st.cache_resource
def get_log_collection():
    client = MongoClient(st.secrets["mongodb"]["uri"])
    db = client["photo_update_db"]
    return db["access_logs"]

def log_access(lat=None, lon=None):
    """
    Guarda un log de acceso con coordenadas y fecha/hora de Colombia.
    """
    col = get_log_collection()
    doc = {
        "evento": "acceso_app",
        "fecha": datetime.now(colombia_tz),
        "latitud": lat if lat is not None else "Sin dato",
        "longitud": lon if lon is not None else "Sin dato",
    }
    col.insert_one(doc)

def get_access_logs(limit=20):
    col = get_log_collection()
    cursor = col.find({"evento": "acceso_app"}).sort("fecha", -1).limit(limit)
    return list(cursor)
