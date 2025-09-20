# db.py
import streamlit as st
from pymongo import MongoClient

@st.cache_resource
def get_client():
    """
    Crear y cachear único cliente MongoDB para evitar reconexiones innecesarias.
    """
    uri = st.secrets["mongodb"]["uri"]
    return MongoClient(uri)

def get_collection():
    """
    Retorna la colección de MongoDB configurada en secretos.
    """
    client = get_client()
    db = client[st.secrets["mongodb"]["db"]]
    return db[st.secrets["mongodb"]["collection"]]

def save_photo(url: str, hash_value: str):
    """
    Inserta un nuevo documento con url y hash.
    """
    col = get_collection()
    col.insert_one({"photo_url": url, "hash": hash_value})

def get_last_hash():
    """
    Recupera el último hash almacenado (ordenado por _id descendente).
    """
    col = get_collection()
    latest = col.find_one(sort=[('_id', -1)])
    if latest and "hash" in latest:
        return latest["hash"]
    return None

def get_last_photo_url():
    """
    Recupera la última url guardada, para usarla en la app si se quiere.
    """
    col = get_collection()
    latest = col.find_one(sort=[('_id', -1)])
    if latest and "photo_url" in latest:
        return latest["photo_url"]
    return None
