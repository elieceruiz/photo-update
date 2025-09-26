# db.py
# ==============================
# Manejo de conexión y operaciones MongoDB
# ==============================

import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import pytz

# Zona horaria local (Bogotá)
colombia = pytz.timezone("America/Bogota")

# ==============================
# Conexión MongoDB
# ==============================

@st.cache_resource
def get_client():
    """
    Crea y cachea un cliente MongoDB usando la URI guardada en st.secrets.
    Retorna None si no está configurado.
    """
    uri = st.secrets.get("mongodb", {}).get("uri", "")
    return MongoClient(uri) if uri else None


def get_db():
    """
    Obtiene el objeto de base de datos definido en st.secrets["mongodb"]["db"].
    Default: "photo_update_db".
    """
    client = get_client()
    if client is not None:
        db_name = st.secrets.get("mongodb", {}).get("db", "photo_update_db")
        return client[db_name]
    return None


def get_collection():
    """
    Obtiene la colección principal de historial de fotos.
    Default: "history".
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
    Inserta un registro en la colección `access_log`.
    
    Campos:
      - ts  : fecha y hora (Bogotá)
      - lat : latitud
      - lon : longitud
      - acc : precisión en metros
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
    Devuelve lista de registros de la colección `access_log`,
    ordenados cronológicamente (ascendente).
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
    Devuelve el último registro insertado en la colección principal (history).
    """
    col = get_collection()
    if col is not None:
        return col.find_one(sort=[("_id", -1)])
    return None


def insert_photo_record(photo_url, hash_value, checked_at=None, geo_data=None):
    """
    Inserta un nuevo registro en la colección principal (history).

    Args:
        photo_url (str)   : URL de la foto
        hash_value (str)  : hash SHA256 de la URL
        checked_at (datetime|None): fecha de verificación.  
            - Si es None → se usa datetime.utcnow() (con tz=UTC).  
            - Si viene naive (sin tz) → se asume UTC.  
            - Siempre se guarda en UTC para consistencia.
        geo_data (dict|None): diccionario con geodatos opcionales, ej:
            {"lat": 6.2442, "lon": -75.5812, "acc": 12.0}
    """
    col = get_collection()
    if col is not None:
        # Normalizar fecha → siempre UTC
        if checked_at is None:
            checked_at = datetime.utcnow().replace(tzinfo=pytz.UTC)
        elif checked_at.tzinfo is None:
            checked_at = checked_at.replace(tzinfo=pytz.UTC)
        else:
            checked_at = checked_at.astimezone(pytz.UTC)

        # Construcción del documento
        record = {
            "photo_url": photo_url,
            "hash": hash_value,
            "checked_at": checked_at,  # UTC estándar
        }

        # Si hay geodatos, anexar
        if geo_data:
            record["lat"] = geo_data.get("lat")
            record["lon"] = geo_data.get("lon")
            record["acc"] = geo_data.get("acc")

        # Insertar en Mongo
        col.insert_one(record)