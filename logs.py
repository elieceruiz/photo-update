# logs.py
import streamlit as st
from datetime import datetime
from pymongo import MongoClient

@st.cache_resource
def get_log_collection():
    """
    Devuelve la colección 'access_logs' de la DB 'photo_update_db'.
    """
    client = MongoClient(st.secrets["mongodb"]["uri"])
    db = client["photo_update_db"]
    return db["access_logs"]

def log_access(lat=None, lon=None):
    """
    Inserta un evento de acceso a la aplicación con coordenadas y fecha.
    """
    col = get_log_collection()
    doc = {
        "evento": "acceso_app",
        "fecha": datetime.now(),
        "latitud": lat,
        "longitud": lon,
    }
    col.insert_one(doc)

def get_access_logs(limit=20):
    """
    Recupera los últimos accesos registrados.
    """
    col = get_log_collection()
    cursor = col.find({"evento": "acceso_app"}).sort("fecha", -1).limit(limit)
    return list(cursor)
