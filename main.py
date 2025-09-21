# main.py
import streamlit as st
from pymongo import MongoClient
import hashlib
import requests
import base64
import pytz
from datetime import datetime
from streamlit_js_eval import get_geolocation

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Photo Update", layout="centered")

colombia = pytz.timezone("America/Bogota")

MONGO_URI = st.secrets["mongo"]["uri"]
DB_NAME = st.secrets["mongo"]["db"]
SEED_URL = st.secrets["seed"]["photo_url"]

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# =========================
# HELPERS
# =========================
def download_image(url: str) -> bytes:
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.content

def calculate_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

def log_access(lat=None, lon=None):
    db.access_log.insert_one({
        "ts": datetime.now(colombia),
        "lat": lat,
        "lon": lon
    })

# =========================
# STATE INIT
# =========================
if "access_logged" not in st.session_state:
    st.session_state.access_logged = False
if "geo_data" not in st.session_state:
    st.session_state.geo_data = None

# =========================
# UI HEADER
# =========================
st.title("📸 Photo Update")

# =========================
# GEOLOCATION (JS + Browser)
# =========================
if not st.session_state.access_logged:
    st.info("🌍 Intentando obtener ubicación desde tu navegador (se pedirá permiso)...")

    geo = get_geolocation()

    if geo:
        if "coords" in geo:
            lat = geo["coords"]["latitude"]
            lon = geo["coords"]["longitude"]
            acc = geo["coords"].get("accuracy", "?")

            st.success(f"📍 Ubicación detectada: {lat:.6f}, {lon:.6f} (±{acc} m)")
            log_access(lat=lat, lon=lon)
            st.session_state.geo_data = {"lat": lat, "lon": lon, "accuracy": acc}
            st.session_state.access_logged = True

        elif "error" in geo:
            st.warning(f"⚠️ Error navegador: {geo['error']}")
            log_access(lat=None, lon=None)
            st.session_state.access_logged = True
    else:
        st.info("⌛ Esperando respuesta del navegador...")

# =========================
# DB: LATEST PHOTO
# =========================
latest = db.photos.find_one(sort=[("_id", -1)])

if latest:
    st.subheader("🔍 Inspector de estado")
    st.json({
        "Último Hash": latest.get("hash"),
        "Última verificación": latest.get("checked_at", "Nunca"),
        "Ubicación": st.session_state.geo_data if st.session_state.geo_data else "No detectado"
    })

    st.image(latest["photo_url"], caption="Miniatura actual")
else:
    st.warning("⚠️ No hay fotos registradas todavía en la base de datos.")

# =========================
# CHECK & UPDATE
# =========================
if st.button("🔄 Verificar foto ahora"):
    try:
        img = download_image(SEED_URL)
        new_hash = calculate_hash(img)

        if not latest or new_hash != latest["hash"]:
            db.photos.insert_one({
                "photo_url": SEED_URL,
                "hash": new_hash,
                "checked_at": datetime.now(colombia)
            })
            st.success("✅ Nueva foto detectada y guardada en MongoDB.")
        else:
            st.info("ℹ️ No hubo cambios en la foto.")

    except Exception as e:
        st.error(f"❌ Error al verificar foto: {e}")
