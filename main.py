# main.py
import streamlit as st
from datetime import datetime, timedelta
import pytz
import requests
import pydeck as pdk
import pandas as pd

from checker import get_image_bytes, has_photo_changed
from db import save_photo, get_last_hash, get_last_photo_url
from notifier import send_whatsapp
from logs import log_access, get_access_logs
from streamlit_geolocation import streamlit_geolocation

# ==============================
# Configuración inicial
# ==============================
st.set_page_config(page_title="📸 Photo Update", layout="wide")
st.title("📸 Photo Update")

colombia_tz = pytz.timezone("America/Bogota")

# --- Inicializar estados ---
if "last_hash" not in st.session_state:
    st.session_state.last_hash = get_last_hash()
if "photo_url" not in st.session_state:
    st.session_state.photo_url = get_last_photo_url() or ""
if "notified_hash" not in st.session_state:
    st.session_state.notified_hash = None
if "last_checked" not in st.session_state:
    st.session_state.last_checked = datetime.min
if "access_logged" not in st.session_state:
    st.session_state.access_logged = False


# ==============================
# Función: obtener ubicación robusta
# ==============================
def get_location_with_fallback():
    """Intenta: componente → IP → input manual. Retorna (lat, lon, source)."""

    # 1) Componente geolocation
    try:
        location = streamlit_geolocation()
    except Exception:
        location = None

    if location:
        lat, lon = None, None
        if isinstance(location.get("latitude"), (float, int)) and isinstance(location.get("longitude"), (float, int)):
            lat, lon = float(location["latitude"]), float(location["longitude"])
        elif isinstance(location.get("coords"), dict):
            coords = location["coords"]
            try:
                lat = float(coords.get("latitude"))
                lon = float(coords.get("longitude"))
            except Exception:
                lat, lon = None, None

        if lat is not None and lon is not None:
            return lat, lon, "componente"

    # 2) Fallback por IP
    try:
        r = requests.get("https://ipapi.co/json/", timeout=5)
        if r.status_code == 200:
            data = r.json()
            lat, lon = data.get("latitude"), data.get("longitude")
            if lat and lon:
                return float(lat), float(lon), "ipapi"
    except Exception:
        pass

    # 3) Input manual
    st.warning("⚠️ No se pudo obtener ubicación automática. Ingresa coordenadas manualmente.")
    lat_input = st.number_input("Latitud (ej: 6.244203)", format="%.6f", value=0.0)
    lon_input = st.number_input("Longitud (ej: -75.581215)", format="%.6f", value=0.0)

    if lat_input != 0.0 or lon_input != 0.0:
        return float(lat_input), float(lon_input), "manual"

    return None, None, "ninguna"


# ==============================
# Detectar y registrar ubicación
# ==============================
if not st.session_state.access_logged:
    with st.spinner("Detectando ubicación..."):
        lat, lon, source = get_location_with_fallback()
        if lat is not None and lon is not None:
            st.success(f"Ubicación detectada ({source}): lat {lat:.6f}, lon {lon:.6f}")
            log_access(lat=lat, lon=lon)
        else:
            st.error("No se obtuvo ubicación. Registrando acceso sin coordenadas.")
            log_access(lat=None, lon=None)
        st.session_state.access_logged = True


# ==============================
# Inspector de estado
# ==============================
st.subheader("🔍 Inspector de estado")

col1, col2 = st.columns(2)
with col1:
    st.metric("Último Hash", st.session_state.last_hash or "—")
with col2:
    if st.session_state.last_checked > datetime.min:
        st.metric("Última verificación", st.session_state.last_checked.strftime("%Y-%m-%d %H:%M:%S"))
    else:
        st.metric("Última verificación", "Nunca")

# Mostrar miniatura
image_bytes = get_image_bytes(st.session_state.photo_url) if st.session_state.photo_url else None
if image_bytes:
    st.image(image_bytes, caption="Miniatura actual")
else:
    st.warning("No se pudo cargar la miniatura desde la URL guardada.")
    nueva_url = st.text_input("👉 Ingresa nueva URL de miniatura Instagram")
    if nueva_url and nueva_url != st.session_state.photo_url:
        st.session_state.photo_url = nueva_url
        st.info("✅ URL actualizada. Presiona 'Verificar actualización'")


# ==============================
# Historial de accesos
# ==============================
st.subheader("📜 Historial de accesos recientes")

logs = get_access_logs(limit=20)
data = []
for log in logs:
    fecha = log.get("fecha")
    if isinstance(fecha, datetime):
        fecha = fecha.astimezone(colombia_tz).strftime("%Y-%m-%d %H:%M:%S")
    lat = log.get("latitud")
    lon = log.get("longitud")
    data.append({"Fecha": fecha, "Latitud": lat, "Longitud": lon})

df_logs = pd.DataFrame(data)
st.dataframe(df_logs)

# Mostrar mapa si hay coords válidas
df_map = df_logs.dropna(subset=["Latitud", "Longitud"])
if not df_map.empty:
    st.subheader("🗺️ Mapa de accesos")
    deck = pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state=pdk.ViewState(
            latitude=df_map["Latitud"].mean(),
            longitude=df_map["Longitud"].mean(),
            zoom=6
        ),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=df_map,
                get_position="[Longitud, Latitud]",
                get_radius=10000,
                pickable=True,
            )
        ],
    )
    st.pydeck_chart(deck)


# ==============================
# Verificar cambios en la foto
# ==============================
st.subheader("📡 Verificación de foto")

min_interval = timedelta(minutes=10)
if st.button("Verificar actualización"):
    now = datetime.now(colombia_tz)
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
                st.success(f"✅ Notificación enviada! SID: {sid}")
            except Exception as e:
                st.error(f"❌ No se pudo enviar la notificación: {e}")
        else:
            st.info("ℹ️ No hay cambios en la foto o ya se notificó esta imagen.")

# Mostrar última verificación
if st.session_state.last_checked > datetime.min:
    st.caption(f"Última verificación: {st.session_state.last_checked.strftime('%Y-%m-%d %H:%M:%S')}")
