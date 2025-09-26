# main.py
# ==============================
# Importaciones
# ==============================
import streamlit as st
from datetime import datetime
import pytz
import pandas as pd

# Módulos locales
from geolocation import handle_geolocation
from photo_checker import check_and_update_photo, download_image
from db import get_latest_record, get_access_logs
from geo_utils import formato_gms_con_hemisferio
from url_handler import show_url_input, process_new_url

# ==============================
# Configuración inicial
# ==============================
st.set_page_config(page_title="📸 Update", layout="centered")
colombia = pytz.timezone("America/Bogota")

# Variables en sesión
if "access_logged" not in st.session_state:
    st.session_state.access_logged = False
if "geo_data" not in st.session_state or st.session_state.geo_data is None:
    st.session_state.geo_data = None
if "show_input" not in st.session_state:
    st.session_state.show_input = False

# ==============================
# Título
# ==============================
st.title("📸 Update")

# ==============================
# Cargar datos iniciales
# ==============================
with st.spinner("Cargando ubicación y datos, por favor espere..."):
    handle_geolocation(st.session_state)
    latest = get_latest_record()

# ==============================
# Si hay registro previo en Mongo
# ==============================
if latest:
    st.subheader("🔍 Inspector de estado")

    # Fecha última verificación
    checked_at = latest.get("checked_at")
    if isinstance(checked_at, datetime):
        if checked_at.tzinfo is None:
            checked_at = checked_at.replace(tzinfo=pytz.UTC)
        checked_at_str = checked_at.astimezone(colombia).strftime("%d %b %y %H:%M")
    else:
        checked_at_str = "❌ No disponible"

    # GeoData
    if st.session_state.geo_data and "lat" in st.session_state.geo_data and "lon" in st.session_state.geo_data:
        lat = st.session_state.geo_data["lat"]
        lon = st.session_state.geo_data["lon"]
        lat_gms_str, lon_gms_str = formato_gms_con_hemisferio(lat, lon)
    else:
        lat = lon = None
        lat_gms_str = lon_gms_str = None

    # Inspector JSON
    st.json({
        "Último Hash": latest.get("hash") or latest.get("hash_value", "❌ No disponible"),
        "Última verificación": checked_at_str,
        "Ubicación actual": {
            "decimal": {
                "lat": lat if lat is not None else "No detectada",
                "lon": lon if lon is not None else "No detectada",
            },
            "GMS": {
                "lat": lat_gms_str if lat_gms_str else "No detectada",
                "lon": lon_gms_str if lon_gms_str else "No detectada",
            }
        }
    })

    # ==============================
    # Input condicional y procesamiento
    # ==============================
    url_mongo, nuevo_url = show_url_input(latest, st.session_state.geo_data)
    process_new_url(url_mongo, nuevo_url, st.session_state.geo_data)

    # ==============================
    # Mostrar imagen
    # ==============================
    try:
        if url_mongo:
            img_bytes = download_image(url_mongo)
            if img_bytes:
                st.image(img_bytes, caption="Miniatura actual")
            else:
                st.error("❌ No se pudo cargar la imagen")
        else:
            st.warning("⚠️ No hay URL de foto en el último registro")
    except Exception as e:
        st.error(f"❌ Error: {e}")

# ==============================
# Si no hay registros previos
# ==============================
else:
    st.warning("⚠️ No hay fotos registradas en la base de datos.")
    url_mongo, nuevo_url = show_url_input(None, st.session_state.geo_data)
    process_new_url(url_mongo, nuevo_url, st.session_state.geo_data)

# ==============================
# Verificación manual
# ==============================
if st.button("🔄 Verificar foto ahora"):
    changed, msg = check_and_update_photo()
    if changed:
        st.success(msg)
        st.session_state.show_input = True   # mostrar input si hubo cambio
    else:
        st.info(msg)
        st.session_state.show_input = False  # ocultar input si no hubo cambio

# ==============================
# Historial de accesos
# ==============================
logs = get_access_logs()
if logs:
    data = []
    for l in logs:
        ts = l["ts"].astimezone(colombia).strftime("%d %b %y %H:%M")
        data.append({
            "Fecha": ts,
            "Lat": f"{l.get('lat'):.6f}" if l.get("lat") else None,
            "Lon": f"{l.get('lon'):.6f}" if l.get("lon") else None,
            "±m": f"{int(l.get('acc'))}" if l.get("acc") else None,
        })
    df = pd.DataFrame(data)
    df.index = range(1, len(df) + 1)
    df = df.iloc[::-1]
    st.subheader("📜 Historial de accesos")
    st.dataframe(df, use_container_width=True)
