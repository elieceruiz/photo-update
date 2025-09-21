# main.py
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import json
import streamlit.components.v1 as components

from checker import get_image_bytes, has_photo_changed
from db import save_photo, get_last_hash, get_last_photo_url
from notifier import send_whatsapp
from logs import log_access, get_access_logs

st.set_page_config(page_title="Photo Update", layout="centered")
st.title("📸 Photo Update con geolocalización inline")

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

# =========================
# Geolocalización con inline JS
# =========================
if not st.session_state.access_logged:
    st.info("🌍 Intentando obtener ubicación desde tu navegador (se pedirá permiso)...")

    geo_html = """
    <script>
    const send = (data) => {
        const streamlitEvent = new CustomEvent("streamlit:componentReady", { detail: { value: JSON.stringify(data) } });
        window.parent.document.dispatchEvent(streamlitEvent);
    };

    function success(pos) {
        const data = {
            lat: pos.coords.latitude,
            lon: pos.coords.longitude,
            accuracy: pos.coords.accuracy
        };
        send(data);
    }

    function error(err) {
        const data = { error: err.message || err.code };
        send(data);
    }

    navigator.geolocation.getCurrentPosition(success, error, {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
    });
    </script>
    """

    components.html(geo_html, height=0)

    # Fallback temporal: pedimos manual si no llegó nada aún
    if st.session_state.geo_data is None:
        st.info("⌛ Esperando respuesta del navegador...")
    else:
        res = st.session_state.geo_data
        if "error" in res:
            st.warning(f"⚠️ Error navegador: {res['error']}")
            log_access(lat=None, lon=None)
            st.session_state.access_logged = True
        else:
            lat, lon = res["lat"], res["lon"]
            acc = res.get("accuracy", "?")
            st.success(f"📍 Ubicación detectada: {lat}, {lon} (±{acc} m)")
            log_access(lat=lat, lon=lon)
            st.session_state.access_logged = True

# =========================
# Inspector
# =========================
st.subheader("🔍 Inspector de estado")
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
