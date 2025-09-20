import streamlit as st
from pymongo import MongoClient

def get_collection():
    uri = st.secrets["mongodb"]["uri"]
    db_name = st.secrets["mongodb"]["db"]
    collection_name = st.secrets["mongodb"]["collection"]

    client = MongoClient(uri)
    db = client[db_name]
    return db[collection_name]

def save_photo(url: str):
    col = get_collection()
    col.insert_one({"photo_url": url})
