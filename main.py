# main.py
import streamlit as st
from pymongo import MongoClient
import hashlib
import requests
import pytz
from datetime import datetime, timedelta
from streamlit_js_eval import get_geolocation
import pandas as pd

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Photo Update", layout="centered")

colombia = pytz.timezone("America/Bogota")

MONGO_URI = st.secrets.get("mongodb", {}).get("uri", "")
DB_NAME = st.secrets.get("mongodb", {}).get("db", "photo_update_db")
COLLECTION = st.secrets.get("mongodb", {}).get("collection", "history")

# Semilla inicial desde secrets.toml
INITIAL_URL = st.secrets.get("initial_photo", {}).get("url", "")
INITIAL_HASH = st.secrets.get("initial_photo", {}).get("hash", "")

client = MongoClient(MONGO_URI) if MONGO_URI else None
db = client[DB_NAME] if client else None

# =========================
# HELPERS
# =========================
def download_image(url: str) -> bytes:
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        raise RuntimeError(f"Error al descargar imagen: {e}")

def calculate_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

def log_access(lat=None, lon=None):
    if db is not None:
        db.access_log.insert_one({
            "ts": datetime.now(colombia),
            "lat": lat,
            "lon": lon
        })

def get_last_photo():
    if db is not None:
        return db[COLLECTION].find_one(sort=[("_id", -1)])
    return None

# =========================
# STATE INIT
# =========================
if "access_logged" not in st.session_state:
    st.session_state.access_logged = False
if "geo_data" not in st.session_state:
    st.session_state.geo_data = None
if "last_checked" not in st.session_state:
    st.session_state.last_checked = datetime.min

# =========================
# UI HEADER
# =========================
st.title("📸 Photo Update")

# =========================
# GEOLOCATION
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
# DB: LATEST PHOTO OR INITIAL
# =========================
latest = get_last_photo()

# Si DB está vacía y hay semilla, insertarla
if not latest and INITIAL_URL and INITIAL_HASH and db is not None:
    db[COLLECTION].insert_one({
        "photo_url": INITIAL_URL,
        "hash": INITIAL_HASH,
        "checked_at": datetime.now(colombia),
        "lat": st.session_state.geo_data["lat"] if st.session_state.geo_data else None,
        "lon": st.session_state.geo_data["lon"] if st.session_state.geo_data else None,
        "source": "seed"
    })
    latest = get_last_photo()
    st.success("🌱 Foto inicial registrada desde secrets.toml.")

# Mostrar inspector
if latest:
    st.subheader("🔍 Inspector de estado")
    st.json({
        "Último Hash": latest.get("hash"),
        "Última verificación": latest.get("checked_at", "Nunca"),
        "Ubicación": st.session_state.geo_data if st.session_state.geo_data else "No detectado",
        "Total cambios": db[COLLECTION].count_documents({})
    })

# Mostrar miniatura
photo_url = latest["photo_url"] if latest else INITIAL_URL
if photo_url:
    st.image(photo_url, caption="Miniatura actual")
else:
    st.warning("⚠️ No hay URL de foto configurada ni registro previo en Mongo.")

# =========================
# CHECK & UPDATE
# =========================
min_interval = timedelta(minutes=10)

if st.button("🔄 Verificar foto ahora"):
    now = datetime.now(colombia)
    if now - st.session_state.last_checked < min_interval:
        st.warning(f"⌛ Espera {int(min_interval.total_seconds()/60)} minutos entre chequeos.")
    else:
        st.session_state.last_checked = now
        if not photo_url:
            st.error("❌ No hay URL de foto configurada ni en secrets.toml ni en Mongo.")
        else:
            try:
                img = download_image(photo_url)
                new_hash = calculate_hash(img)

                if not latest or new_hash != latest["hash"]:
                    db[COLLECTION].insert_one({
                        "photo_url": photo_url,
                        "hash": new_hash,
                        "checked_at": datetime.now(colombia),
                        "lat": st.session_state.geo_data["lat"] if st.session_state.geo_data else None,
                        "lon": st.session_state.geo_data["lon"] if st.session_state.geo_data else None,
                        "source": "manual"
                    })
                    st.success("✅ Nueva foto detectada y guardada en MongoDB.")
                else:
                    st.info("ℹ️ No hubo cambios en la foto.")
            except Exception as e:
                st.error(f"❌ Error al verificar foto: {e}")

# =========================
# HISTORIAL DE ACCESOS
# =========================
if db is not None:
    st.subheader("📜 Historial de accesos recientes")
    logs = list(db.access_log.find().sort("ts", -1).limit(10))
    if logs:
        df = pd.DataFrame([{
            "Fecha": l["ts"].strftime("%Y-%m-%d %H:%M:%S"),
            "Lat": l.get("lat"),
            "Lon": l.get("lon")
        } for l in logs])
        st.dataframe(df)
