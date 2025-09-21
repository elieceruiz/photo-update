# main.py
import streamlit as st
from datetime import datetime
import pytz
import pandas as pd

from geolocation import handle_geolocation
from photo_checker import check_and_update_photo, download_image
from db import get_latest_record, get_access_logs
from geo_utils import formato_gms_con_hemisferio

st.set_page_config(page_title="📸 Update", layout="centered")
colombia = pytz.timezone("America/Bogota")

if "access_logged" not in st.session_state:
    st.session_state.access_logged = False
if "geo_data" not in st.session_state or st.session_state.geo_data is None:
    st.session_state.geo_data = None

st.title("📸 Update")

handle_geolocation(st.session_state)

latest = get_latest_record()

if latest:
    st.subheader("🔍 Inspector de estado")
    checked_at = latest.get("checked_at")
    if isinstance(checked_at, datetime):
        if checked_at.tzinfo is None:
            checked_at = checked_at.replace(tzinfo=pytz.UTC)
        checked_at = checked_at.astimezone(colombia).strftime("%d %b %y %H:%M")

    # Variables para mostrar coordenadas en decimal y GMS
    if st.session_state.geo_data and "lat" in st.session_state.geo_data and "lon" in st.session_state.geo_data:
        lat = st.session_state.geo_data["lat"]
        lon = st.session_state.geo_data["lon"]
        lat_gms_str, lon_gms_str = formato_gms_con_hemisferio(lat, lon)
    else:
        lat = None
        lon = None
        lat_gms_str = None
        lon_gms_str = None

    st.json({
        "Último Hash": latest.get("hash"),
        "Última verificación": checked_at or "Nunca",
        "Ubicación": {
            "decimal": {
                "lat": lat,
                "lon": lon,
            },
            "GMS": {
                "lat": lat_gms_str,
                "lon": lon_gms_str,
            }
        }
    })

    try:
        img_bytes = download_image(latest["photo_url"])
        if img_bytes:
            st.image(img_bytes, caption="Miniatura actual")
        else:
            st.error("❌ No se pudo cargar la imagen")
    except Exception as e:
        st.error(f"❌ Error: {e}")
else:
    st.warning("⚠️ No hay fotos registradas en la base de datos.")

if st.button("🔄 Verificar foto ahora"):
    changed, msg = check_and_update_photo()
    if changed:
        st.success(msg)
    else:
        st.info(msg)

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
