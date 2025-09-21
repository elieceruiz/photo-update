# main.py
import streamlit as st
from datetime import datetime, timedelta
from pymongo import MongoClient
from checker import get_image_bytes, has_photo_changed
from notifier import send_whatsapp
from streamlit_geolocation import streamlit_geolocation
import pandas as pd
import pytz

# =========================
# CONFIGURACIÓN
# =========================
st.set_page_config(page_title="📸 Photo Update", layout="centered")
st.title("📸 Photo Update")

colombia = pytz.timezone("America/Bogota")

# =========================
# CONEXIÓN DB
# =========================
MONGO_URI = st.secrets["mongodb"]["uri"]
DB_NAME = st.secrets["mongodb"]["db"]
COLLECTION = st.secrets["mongodb"].get("collection", "history")

@st.cache_resource
def get_client():
    return MongoClient(MONGO_URI)

client = get_client()
db = client[DB_NAME] if client else None

# =========================
# FUNCIONES
# =========================
def log_access(lat=None, lon=None):
    if db is not None:
        db.access_log.insert_one({
            "ts": datetime.now(colombia),
            "lat": lat,
            "lon": lon
        })

def get_last_photo():
    if db is not None:
        latest = db[COLLECTION].find_one(sort=[("_id", -1)])
        return latest
    return None

# =========================
# ESTADOS INICIALES
# =========================
if "last_hash" not in st.session_state:
    last = get_last_photo()
    st.session_state.last_hash = last["hash"] if last else None

if "photo_url" not in st.session_state:
    last = get_last_photo()
    st.session_state.photo_url = last["photo_url"] if last else st.secrets.get("seed", {}).get("photo_url", "")

if "notified_hash" not in st.session_state:
    st.session_state.notified_hash = None

if "last_checked" not in st.session_state:
    st.session_state.last_checked = datetime.min

if "access_logged" not in st.session_state:
    st.session_state.access_logged = False

# =========================
# GEOLOCALIZACIÓN
# =========================
st.write("🌍 Intentando obtener ubicación desde tu navegador (se pedirá permiso)...")

if not st.session_state.access_logged:
    location = streamlit_geolocation()
    if location and "latitude" in location and "longitude" in location:
        lat = location["latitude"]
        lon = location["longitude"]
        acc = location.get("accuracy", "?")
        st.success(f"📍 Ubicación detectada: {lat}, {lon} (±{acc} m)")
        log_access(lat=lat, lon=lon)
        st.session_state.access_logged = True
    else:
        st.warning("⚠️ No se pudo obtener ubicación o se denegó el permiso.")

# =========================
# MOSTRAR MINIATURA INSTAGRAM
# =========================
image_bytes = get_image_bytes(st.session_state.photo_url) if st.session_state.photo_url else None
if image_bytes:
    st.image(image_bytes, caption="Miniatura actual")
else:
    st.warning("⚠️ No se pudo cargar la miniatura desde la URL guardada.")
    nueva_url = st.text_input("🔗 Ingrese nueva URL de miniatura Instagram")
    if nueva_url and nueva_url != st.session_state.photo_url:
        st.session_state.photo_url = nueva_url
        st.info("✅ URL actualizada. Presiona 'Verificar actualización'.")

# =========================
# HISTORIAL DE ACCESOS
# =========================
if db is not None:
    st.subheader("📜 Historial de accesos recientes")
    logs = list(db.access_log.find().sort("ts", -1).limit(10))
    data = []
    for log in logs:
        fecha = log.get("ts").strftime("%Y-%m-%d %H:%M:%S")
        lat = log.get("lat")
        lon = log.get("lon")
        data.append({"Fecha": fecha, "Latitud": lat, "Longitud": lon})
    if data:
        df_logs = pd.DataFrame(data)
        st.dataframe(df_logs)

# =========================
# BOTÓN: VERIFICAR CAMBIOS
# =========================
min_interval = timedelta(minutes=10)
if st.button("🔍 Verificar actualización"):
    now = datetime.now(colombia)
    if now - st.session_state.last_checked < min_interval:
        st.warning(f"⌛ Espera {int(min_interval.total_seconds()/60)} minutos entre chequeos.")
    else:
        st.session_state.last_checked = now
        changed, current_hash = has_photo_changed(st.session_state.photo_url, st.session_state.last_hash)
        if changed and st.session_state.notified_hash != current_hash:
            st.session_state.last_hash = current_hash
            st.session_state.notified_hash = current_hash
            if db is not None:
                db[COLLECTION].insert_one({
                    "photo_url": st.session_state.photo_url,
                    "hash": current_hash,
                    "ts": datetime.now(colombia)
                })
            try:
                sid = send_whatsapp(f"📸 Nueva foto detectada: {st.session_state.photo_url}")
                st.success(f"✅ Notificación enviada! SID: {sid}")
            except Exception as e:
                st.error(f"❌ No se pudo enviar notificación: {e}")
        else:
            st.info("ℹ️ No hay cambios en la foto o ya se notificó esta imagen.")

# =========================
# ÚLTIMA VERIFICACIÓN
# =========================
if st.session_state.last_checked > datetime.min:
    st.write(f"🕒 Última verificación: {st.session_state.last_checked.strftime('%Y-%m-%d %H:%M:%S')}")
