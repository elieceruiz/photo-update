# db.py
import streamlit as st
from pymongo import MongoClient

@st.cache_resource
def get_client():
    uri = st.secrets["mongodb"]["uri"]
    return MongoClient(uri)

def get_collection():
    client = get_client()
    db = client["photo_update_db"]  # Aquí fijo el nombre de DB
    return db["history"]  # Aquí fijo la colección como "history"

def save_photo(url: str, hash_value: str):
    col = get_collection()
    col.insert_one({"photo_url": url, "hash": hash_value})

def get_last_hash():
    col = get_collection()
    latest = col.find_one(sort=[('_id', -1)])
    return latest["hash"] if latest and "hash" in latest else None

def get_last_photo_url():
    col = get_collection()
    latest = col.find_one(sort=[('_id', -1)])
    return latest["photo_url"] if latest and "photo_url" in latest else None
