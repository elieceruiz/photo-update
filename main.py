# =========================
# main.py
# =========================
# App en Streamlit para registrar actualizaciones de fotos, verificar hashes,
# guardar URLs y ubicaciones en MongoDB, y mostrar un inspector de estado.
# =========================

import streamlit as st
from pymongo import MongoClient
import hashlib
import requests
import pytz
from datetime import datetime
from streamlit_js_eval import get_geolocation
import pandas as pd
import json

# =========================
# CONFIGURACIÓN INICIAL
# =========================
st.set_page_config(page_title="Photo Update", layout="centered")
colombia = pytz.timezone("America/Bogota")

# =========================
# CONEXIÓN A MONGO
# =========================
# Nota: Ajusta con tu string de conexión real.
client = MongoClient("mongodb://localhost:27017/")
db = client["photo_update_db"]
collection = db["photos"]

# =========================
# FUNCIONES AUXILIARES
# =========================

def calcular_hash(url):
    """
    Calcula el hash SHA256 de la imagen descargada desde la URL.
    Devuelve el hash en hexadecimal.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return hashlib.sha256(response.content).hexdigest()
    except Exception as e:
        st.error(f"⚠️ Error calculando hash: {e}")
        return None


def insert_photo_record(url, hash_value, ultima_verificacion=None, geo_data=None):
    """
    Inserta un nuevo registro en MongoDB con:
    - URL de la imagen
    - Hash calculado
    - Última verificación (timestamp string)
    - Ubicación (geo_data en dict)
    - Fecha de inserción
    """
    try:
        record = {
            "url": url,
            "hash": hash_value,
            "ultima_verificacion": ultima_verificacion,
            "ubicacion": geo_data,
            "fecha": datetime.now(colombia).strftime("%d %b %y %H:%M")
        }
        collection.insert_one(record)
        return True
    except Exception as e:
        st.error(f"💥 Error en insert_photo_record: {e}")
        return False


def obtener_ultimo_registro():
    """
    Obtiene el último registro insertado en MongoDB.
    Si no hay, devuelve None.
    """
    return collection.find_one(sort=[("_id", -1)])


def comparar_urls(url_db, url_nueva):
    """
    Compara 2 URLs analizando sus parámetros GET.
    Devuelve un dict con las diferencias encontradas.
    """
    from urllib.parse import urlparse, parse_qs

    parsed_db = urlparse(url_db)
    parsed_new = urlparse(url_nueva)

    params_db = parse_qs(parsed_db.query)
    params_new = parse_qs(parsed_new.query)

    diferencias = {}
    for key in set(params_db.keys()).union(params_new.keys()):
        val_db = params_db.get(key, ["—"])[0]
        val_new = params_new.get(key, ["—"])[0]
        if val_db != val_new:
            diferencias[key] = {"Mongo": val_db, "Nuevo": val_new}

    return diferencias


def formato_gms(lat, lon):
    """
    Convierte coordenadas decimales en formato Grados, Minutos, Segundos (GMS).
    """
    def to_gms(value, is_lat=True):
        grados = int(abs(value))
        minutos = int((abs(value) - grados) * 60)
        segundos = round(((abs(value) - grados) * 60 - minutos) * 60, 2)
        cardinal = (
            "N" if is_lat and value >= 0 else
            "S" if is_lat else
            "E" if value >= 0 else "W"
        )
        return f"{grados}° {minutos}' {segundos}\" {cardinal}"

    return {
        "lat": to_gms(lat, is_lat=True),
        "lon": to_gms(lon, is_lat=False)
    }

# =========================
# FRONT: INTERFAZ STREAMLIT
# =========================

st.title("📸 Update")
st.subheader("🔍 Inspector de estado")

# --- Obtener último registro de Mongo
ultimo = obtener_ultimo_registro()

if ultimo:
    # Mostrar último hash y verificación
    st.json({
        "Último Hash": ultimo.get("hash"),
        "Última verificación": ultimo.get("ultima_verificacion"),
        "Ubicación": {
            "decimal": ultimo.get("ubicacion"),
            "GMS": (
                formato_gms(
                    ultimo["ubicacion"]["lat"],
                    ultimo["ubicacion"]["lon"]
                )
                if ultimo.get("ubicacion") else None
            )
        }
    })
else:
    st.info("ℹ️ No hay registros previos en MongoDB.")

st.divider()

# --- Input de nueva URL
nuevo_url = st.text_input("✏️ Ingresa nuevo enlace para comparar y registrar")

if nuevo_url:
    if ultimo:
        st.write("🔗 URL en Mongo:")
        st.code(ultimo["url"])

        st.write("🔗 Nueva URL ingresada:")
        st.code(nuevo_url)

        # Comparar parámetros
        diferencias = comparar_urls(ultimo["url"], nuevo_url)

        if diferencias:
            st.error("❌ El link en Mongo es DIFERENTE al nuevo")
            st.write("🔍 Diferencias encontradas por parámetro:")
            st.json(diferencias)
        else:
            st.success("✅ Los enlaces son iguales (parámetros coinciden).")

    # --- Botón para registrar nuevo
    if st.button("Registrar nuevo enlace"):
        nuevo_hash = calcular_hash(nuevo_url)
        if nuevo_hash:
            # Capturar ubicación del navegador
            geo_data = get_geolocation()
            if geo_data:
                st.session_state.geo_data = geo_data
            else:
                st.session_state.geo_data = None

            exito = insert_photo_record(
                nuevo_url,
                nuevo_hash,
                datetime.now(colombia).strftime("%d %b %y %H:%M"),
                st.session_state.geo_data
            )

            if exito:
                st.success("✅ Nuevo enlace registrado en MongoDB.")
            else:
                st.error("❌ No se pudo guardar en Mongo.")