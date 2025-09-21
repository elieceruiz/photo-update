# main.py
import streamlit as st
from pymongo import MongoClient
import hashlib
import requests
import pytz
from datetime import datetime
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

client = MongoClient(MONGO_URI) if MONGO_URI else None
db = client[DB_NAME] if client else None

# =========================
# HELPERS
# =========================
def download_image(url: str) -> bytes:
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.content

def calculate_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

def log_access(lat=None, lon=None, acc=None):
    if db is not None:
        db.access_log.insert_one({
            "ts": datetime.now(colombia),
            "lat": lat,
            "lon": lon,
            "acc": acc
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
# GEOLOCATION
# =========================
if not st.session_state.access_logged:
    geo = get_geolocation()

    if geo:
        if "coords" in geo:
            lat = geo["coords"]["latitude"]
            lon = geo["coords"]["longitude"]
            acc = geo["coords"].get("accuracy", "?")

            st.success(f"📍 Ubicación detectada: {lat:.6f}, {lon:.6f} (±{acc} m)")
            log_access(lat=lat, lon=lon, acc=acc)
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
latest = None
if db is not None:
    latest = db[COLLECTION].find_one(sort=[("_id", -1)])

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
    if not latest:
        st.error("❌ No hay foto inicial en la base de datos.")
    else:
        try:
            img = download_image(latest["photo_url"])
            new_hash = calculate_hash(img)

            if not latest or new_hash != latest["hash"]:
                db[COLLECTION].insert_one({
                    "photo_url": latest["photo_url"],
                    "hash": new_hash,
                    "checked_at": datetime.now(colombia)
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
            "Fecha": l["ts"].strftime("%d %b %y"),
            "Lat": l.get("lat"),
            "Lon": l.get("lon"),
            "±m": l.get("acc")
        } for l in logs])
        # Reordenar para que el más antiguo quede abajo con índice 1
        df = df.iloc[::-1].reset_index(drop=True)
        df.index = df.index + 1
        st.dataframe(df)
