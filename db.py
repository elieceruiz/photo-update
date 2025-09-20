# db.py
import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import pytz

# Zona horaria Colombia
colombia_tz = pytz.timezone("America/Bogota")

@st.cache_resource
def get_client():
    uri = st.secrets["mongodb"]["uri"]
    return MongoClient(uri)

def get_collection():
    client = get_client()
    db = client["photo_update_db"]
    return db["history"]

def save_photo(url: str, hash_value: str):
    """
    Guarda foto (URL + hash + fecha Colombia) en la colección.
    Evita duplicados exactos.
    """
    col = get_collection()
    exists = col.find_one({"photo_url": url, "hash": hash_value})
    if exists:
        return False
    
    doc = {
        "photo_url": url,
        "hash": hash_value,
        "fecha": datetime.now(colombia_tz)
    }
    col.insert_one(doc)
    return True

def get_last_hash():
    col = get_collection()
    latest = col.find_one(sort=[('_id', -1)])
    return latest["hash"] if latest and "hash" in latest else None

def get_last_photo_url():
    col = get_collection()
    latest = col.find_one(sort=[('_id', -1)])
    return latest["photo_url"] if latest and "photo_url" in latest else None

def seed_initial_photo():
    """
    Inserta la semilla inicial desde secrets si la colección está vacía.
    Solo ocurre en la primera ejecución.
    """
    col = get_collection()
    if col.count_documents({}) == 0 and "initial_photo" in st.secrets:
        init_url = st.secrets["initial_photo"].get("url")
        init_hash = st.secrets["initial_photo"].get("hash")
        if init_url and init_hash:
            doc = {
                "photo_url": init_url,
                "hash": init_hash,
                "fecha": datetime.now(colombia_tz)
            }
            col.insert_one(doc)
