# main.py
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

from checker import get_image_bytes, has_photo_changed
from db import save_photo, get_last_hash, get_last_photo_url
from notifier import send_whatsapp
from logs import log_access, get_access_logs

from geo_component import get_geolocation

st.set_page_config(page_title="Photo Update", layout="centered")
st.title("📸 Photo Update con geolocalización real (componente)")

# =========================
# Estados iniciales
# =========================
if "last_hash" not in st.session_state:
    st.session_state.last_hash = get_last_hash()
if "photo_url" not in st.session_state:
    st.session_state.photo_url = get_last_photo_url() or st.secrets.get("INITIAL_PHOTO_URL", "")
if "notified_hash" not in st.session_state:
    st.session_state.notified_hash = None
if "last_checked" not in st.session_state:
    st.session_state.last_checked = datetime.min
if "access_logged" not in st.session_state:
    st.session_state.access_logged = False

# =========================
# Geolocalización
# =========================
if not st.session_state.access_logged:
    st.info("🌍 Intentando obtener ubicación desde tu navegador (se pedirá permiso)...")

    geo = get_geolocation()

    if geo and "lat" in geo and "lon" in geo:
        lat, lon = float(geo["lat"]), float(geo["lon"])
        acc = geo.get("accuracy")
        st.success(f"📍 Ubicación detectada: {lat:.6f}, {lon:.6f} (±{acc} m)")
        log_access(lat=lat, lon=lon)
        st.session_state.access_logged = True
    elif geo and "error" in geo:
        st.warning(f"⚠️ Error navegador: {geo['error']}")
        log_access(lat=None, lon=None)
        st.session_state.access_logged = True
    else:
        st.info("⌛ Esperando respuesta del navegador...")

# =========================
# Foto actual
# =========================
image_bytes = get_image_bytes(st.session_state.photo_url) if st.session_state.photo_url else None
if image_bytes:
    st.image(image_bytes, caption="Miniatura actual")
else:
    st.warning("No se pudo cargar la miniatura desde la URL guardada.")
    nueva_url = st.text_input("Ingrese nueva URL de miniatura Instagram")
    if nueva_url and nueva_url != st.session_state.photo_url:
        st.session_state.photo_url = nueva_url
        st.info("✅ URL actualizada. Presiona 'Verificar actualización'.")

# =========================
# Historial de accesos
# =========================
st.subheader("📜 Historial de accesos recientes")
logs = get_access_logs(limit=10)
data = []
for log in logs:
    fecha = log.get("fecha").strftime("%Y-%m-%d %H:%M:%S")
    data.append({
        "Fecha": fecha,
        "Latitud": log.get("latitud"),
        "Longitud": log.get("longitud")
    })

df_logs = pd.DataFrame(data)
st.dataframe(df_logs)

# =========================
# Botón verificación
# =========================
min_interval = timedelta(minutes=10)
if st.button("Verificar actualización"):
    now = datetime.now()
    if now - st.session_state.last_checked < min_interval:
        st.warning(f"⏳ Espera {int(min_interval.total_seconds()/60)} minutos entre chequeos.")
    else:
        st.session_state.last_checked = now
        changed, current_hash = has_photo_changed(
            st.session_state.photo_url, st.session_state.last_hash
        )
        if changed and st.session_state.notified_hash != current_hash:
            st.session_state.last_hash = current_hash
            st.session_state.notified_hash = current_hash
            save_photo(st.session_state.photo_url, current_hash)
            try:
                sid = send_whatsapp(f"📸 Nueva foto detectada: {st.session_state.photo_url}")
                st.success(f"✅ Notificación enviada! SID: {sid}")
            except Exception as e:
                st.error(f"❌ No se pudo enviar la notificación: {e}")
        else:
            st.info("ℹ️ No hay cambios en la foto o ya se notificó esta imagen.")
