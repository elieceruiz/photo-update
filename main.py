# main.py
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import json

from checker import get_image_bytes, has_photo_changed
from db import save_photo, get_last_hash, get_last_photo_url
from notifier import send_whatsapp
from logs import log_access, get_access_logs

import streamlit.components.v1 as components

st.set_page_config(page_title="Photo Update", layout="centered")
st.title("📸 Photo Update con ubicación desde navegador (JS directo)")

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
if "geo_data" not in st.session_state:
    st.session_state.geo_data = None
if "geo_raw" not in st.session_state:
    st.session_state.geo_raw = None

# =========================
# Detección de ubicación con HTML + JS
# =========================
if not st.session_state.access_logged:
    st.info("🌍 Intentando obtener ubicación desde tu navegador (se pedirá permiso)...")

    # HTML+JS para pedir ubicación y mandarla a Streamlit
    components.html(
        """
        <script>
        const sendCoords = (pos) => {
            const data = {
                lat: pos.coords.latitude,
                lon: pos.coords.longitude,
                accuracy: pos.coords.accuracy
            };
            Streamlit.setComponentValue(JSON.stringify(data)); // ✅ mandar JSON
        };

        const sendError = (err) => {
            const data = {error: err.message || err.code};
            Streamlit.setComponentValue(JSON.stringify(data)); // ✅ mandar error
        };

        navigator.geolocation.getCurrentPosition(sendCoords, sendError, {
            enableHighAccuracy: true,
            timeout: 15000,
            maximumAge: 0
        });
        </script>
        """,
        height=0,
    )

    # Recibir valor
    geo_raw = st.session_state.get("component_value")

    if geo_raw:
        st.session_state.geo_raw = geo_raw  # guardar crudo para debug
        try:
            res = json.loads(geo_raw)
        except Exception:
            st.error(f"⚠️ No se pudo parsear la respuesta del navegador: {geo_raw}")
            res = {}

        if res.get("error"):
            st.warning(f"⚠️ Error navegador: {res['error']}")
            log_access(lat=None, lon=None)
            st.session_state.access_logged = True
        elif "lat" in res and "lon" in res:
            lat, lon = float(res["lat"]), float(res["lon"])
            acc = res.get("accuracy")
            st.success(f"📍 Ubicación detectada: {lat:.6f}, {lon:.6f} (±{acc} m)")
            log_access(lat=lat, lon=lon)
            st.session_state.geo_data = res
            st.session_state.access_logged = True
        else:
            st.error(f"❌ Respuesta inesperada: {res}")
    else:
        st.info("⌛ Esperando respuesta del navegador...")

# =========================
# Inspector de estado
# =========================
st.subheader("🔍 Inspector de estado")
st.write("**Crudo navegador:**", st.session_state.geo_raw)
st.json(st.session_state.geo_data or {"geo": "No detectado"})

# =========================
# Foto
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
# Historial
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
