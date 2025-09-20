# db.py
import streamlit as st
from pymongo import MongoClient
from datetime import datetime

@st.cache_resource
def get_client():
    """
    Devuelve un cliente MongoDB usando la URI de secrets.
    """
    uri = st.secrets["mongodb"]["uri"]
    return MongoClient(uri)

def get_collection():
    """
    Devuelve la colección 'history' de la DB 'photo_update_db'.
    """
    client = get_client()
    db = client["photo_update_db"]
    return db["history"]

def save_photo(url: str, hash_value: str):
    """
    Guarda una foto en la colección con URL, hash y fecha/hora,
    evitando duplicados (misma URL y mismo hash).
    """
    col = get_collection()
    
    # Revisar si ya existe este par (url + hash)
    exists = col.find_one({"photo_url": url, "hash": hash_value})
    if exists:
        return False  # No guarda duplicado
    
    doc = {
        "photo_url": url,
        "hash": hash_value,
        "fecha": datetime.now()
    }
    col.insert_one(doc)
    return True

def get_last_hash():
    """
    Recupera el último hash guardado.
    """
    col = get_collection()
    latest = col.find_one(sort=[('_id', -1)])
    return latest["hash"] if latest and "hash" in latest else None

def get_last_photo_url():
    """
    Recupera la última URL guardada.
    """
    col = get_collection()
    latest = col.find_one(sort=[('_id', -1)])
    return latest["photo_url"] if latest and "photo_url" in latest else None

def get_history(limit=20):
    """
    Devuelve los últimos registros de fotos guardadas.
    """
    col = get_collection()
    cursor = col.find().sort("fecha", -1).limit(limit)
    return list(cursor)
