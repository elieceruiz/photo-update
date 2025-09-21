# main.py
import streamlit as st
from datetime import datetime, timedelta
from checker import get_image_bytes, has_photo_changed
from db import save_photo, get_last_hash, get_last_photo_url, get_access_logs, log_access
from notifier import send_whatsapp
import pandas as pd
import requests

st.set_page_config(page_title="Photo Update", layout="centered")
st.title("📸 Photo Update")

# =========================
# Funciones auxiliares
# =========================
def is_in_colombia(lat, lon):
    return -4.23 <= lat <= 13.38 and -81.73 <= lon <= -66.85

def get_location_with_fallback():
    """Obtiene ubicación: 1) componente navegador, 2) ipapi validando Colombia, 3) manual"""
    # Intentar componente navegador
    try:
        from streamlit_geolocation import streamlit_geolocation
        loc = streamlit_geolocation()
    except Exception as e:
        st.info(f"[DEBUG] No cargó componente navegador: {e}")
        loc = None

    if loc:
        lat, lon = loc.get("latitude"), loc.get("longitude")
        if lat and lon:
            st.info("[DEBUG] Ubicación obtenida del componente navegador")
            return float(lat), float(lon), "componente"

    # Intentar ipapi
    try:
        r = requests.get("https://ipapi.co/json/", timeout=5)
        if r.status_code == 200:
            data = r.json()
            lat, lon = data.get("latitude"), data.get("longitude")
            if lat and lon and is_in_colombia(float(lat), float(lon)):
                st.info("[DEBUG] Ubicación obtenida de ipapi (válida en Colombia)")
                return float(lat), float(lon), "ipapi"
            else:
                st.warning("[DEBUG] ipapi devolvió coordenadas fuera de Colombia, ignoradas")
    except Exception as e:
        st.error(f"[DEBUG] Error al consultar ipapi: {e}")

    # Manual
    st.warning("⚠️ No se pudo obtener ubicación automática válida. Ingresa coordenadas manualmente.")
    lat_input = st.number_input("Latitud (ej: 6.3389)", format="%.6f", value=0.0)
    lon_input = st.number_input("Longitud (ej: -75.5587)", format="%.6f", value=0.0)

    if lat_input != 0.0 or lon_input != 0.0:
        st.info("[DEBUG] Ubicación ingresada manualmente")
        return float(lat_input), float(lon_input), "manual"

    return None, None, "ninguna"

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
# Detectar ubicación
# =========================
if not st.session_state.access_logged:
    with st.spinner("Detectando ubicación automáticamente..."):
        lat, lon, fuente = get_location_with_fallback()
        if lat and lon:
            log_access(lat=lat, lon=lon)
            st.session_state.access_logged = True
            st.success(f"Ubicación detectada ({fuente}): lat {lat}, lon {lon}")
        else:
            st.error("❌ No se pudo obtener la ubicación.")

# =========================
# Inspector de estado
# =========================
st.subheader("🔍 Inspector de estado")

st.write(f"**Último Hash:** {st.session_state.last_hash or 'N/A'}")
st.write(f"**Última verificación:** {st.session_state.last_checked if st.session_state.last_checked > datetime.min else 'Nunca'}")

image_bytes = get_image_bytes(st.session_state.photo_url) if st.session_state.photo_url else None
if image_bytes:
    st.image(image_bytes, caption="Miniatura actual")
else:
    st.warning("No se pudo cargar la miniatura desde la URL guardada.")
    nueva_url = st.text_input("Ingrese nueva URL de miniatura Instagram")
    if nueva_url and nueva_url != st.session_state.photo_url:
        st.session_state.photo_url = nueva_url
        st.info("URL actualizada. Presiona 'Verificar actualización'.")

# =========================
# Historial de accesos
# =========================
st.subheader("📜 Historial de accesos recientes")
logs = get_access_logs(limit=10)
data = []
for log in logs:
    fecha = log.get("fecha").strftime("%Y-%m-%d %H:%M:%S")
    lat = log.get("latitud")
    lon = log.get("longitud")
    data.append({"Fecha": fecha, "Latitud": lat, "Longitud": lon})

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
        changed, current_hash = has_photo_changed(st.session_state.photo_url, st.session_state.last_hash)
        if changed and st.session_state.notified_hash != current_hash:
            st.session_state.last_hash = current_hash
            st.session_state.notified_hash = current_hash
            save_photo(st.session_state.photo_url, current_hash)
            try:
                sid = send_whatsapp(f"📸 Nueva foto detectada: {st.session_state.photo_url}")
                st.success(f"Notificación enviada! SID: {sid}")
            except Exception as e:
                st.error(f"No se pudo enviar la notificación: {e}")
        else:
            st.info("ℹ️ No hay cambios en la foto o ya se notificó esta imagen.")
