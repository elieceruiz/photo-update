# db.py
import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import pytz

colombia = pytz.timezone("America/Bogota")

# ==============================
# Conexión MongoDB
# ==============================
@st.cache_resource
def get_client():
    """
    Retorna el cliente MongoDB a partir de st.secrets["mongodb"]["uri"].
    """
    uri = st.secrets.get("mongodb", {}).get("uri", "")
    return MongoClient(uri) if uri else None

def get_db():
    """
    Obtiene la base de datos definida en st.secrets["mongodb"]["db"] 
    (default: photo_update_db).
    """
    client = get_client()
    if client is not None:
        db_name = st.secrets.get("mongodb", {}).get("db", "photo_update_db")
        return client[db_name]
    return None

def get_collection():
    """
    Obtiene la colección principal de historial de fotos.
    Nombre definido en st.secrets["mongodb"]["collection"] (default: history).
    """
    db = get_db()
    if db is not None:
        col_name = st.secrets.get("mongodb", {}).get("collection", "history")
        return db[col_name]
    return None

# ==============================
# Logs de accesos
# ==============================
def insert_access_log(lat, lon, acc):
    """
    Inserta un registro en la colección access_log con lat/lon/accuracy.
    """
    db = get_db()
    if db is not None:
        db.access_log.insert_one({
            "ts": datetime.now(colombia),
            "lat": lat,
            "lon": lon,
            "acc": acc
        })

def get_access_logs():
    """
    Devuelve la lista de accesos en orden cronológico.
    """
    db = get_db()
    if db is not None:
        cursor = db.access_log.find().sort("ts", 1)
        return list(cursor)
    return []

# ==============================
# Fotos y verificación
# ==============================
def get_latest_record():
    """
    Devuelve el registro más reciente de la colección de fotos.
    """
    col = get_collection()
    if col is not None:
        return col.find_one(sort=[("_id", -1)])
    return None

def insert_photo_record(photo_url, hash_value, checked_at=None, geo_data=None):
    """
    Inserta un nuevo registro de foto en la colección principal (history).
    Guarda:
      - URL
      - hash
      - fecha de verificación (por defecto: ahora en Bogotá)
      - ubicación (si está disponible en geo_data)
    """
    col = get_collection()
    if col is not None:
        # Normalizar fecha
        if checked_at is None:
            checked_at = datetime.now(colombia)
        elif checked_at.tzinfo is None:
            # si no tiene tz, asumimos UTC y convertimos a Bogotá
            checked_at = checked_at.replace(tzinfo=pytz.UTC).astimezone(colombia)
        else:
            # si ya tiene tz, lo pasamos a Bogotá
            checked_at = checked_at.astimezone(colombia)

        record = {
            "photo_url": photo_url,
            "hash": hash_value,
            "checked_at": checked_at
        }
        if geo_data:
            record["lat"] = geo_data.get("lat")
            record["lon"] = geo_data.get("lon")
            record["acc"] = geo_data.get("acc")
        col.insert_one(record)