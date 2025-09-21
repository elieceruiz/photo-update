# db.py
import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import pytz

colombia = pytz.timezone("America/Bogota")

@st.cache_resource
def get_client():
    uri = st.secrets.get("mongodb", {}).get("uri", "")
    return MongoClient(uri) if uri else None

def get_db():
    client = get_client()
    if client:
        db_name = st.secrets.get("mongodb", {}).get("db", "photo_update_db")
        return client[db_name]
    return None

def get_collection():
    db = get_db()
    if db:
        col_name = st.secrets.get("mongodb", {}).get("collection", "history")
        return db[col_name]
    return None

def insert_access_log(lat, lon, acc):
    db = get_db()
    if db:
        db.access_log.insert_one({
            "ts": datetime.now(colombia),
            "lat": lat,
            "lon": lon,
            "acc": acc
        })

def get_latest_record():
    col = get_collection()
    if col:
        return col.find_one(sort=[("_id", -1)])
    return None

def insert_photo_record(photo_url, hash_value):
    col = get_collection()
    if col:
        col.insert_one({
            "photo_url": photo_url,
            "hash": hash_value,
            "checked_at": datetime.now(colombia)
        })

def get_access_logs(limit=100):
    db = get_db()
    if db:
        cursor = db.access_log.find().sort("ts", 1).limit(limit)
        return list(cursor)
    return []
