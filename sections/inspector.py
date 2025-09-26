# sections/inspector.py
import streamlit as st
from datetime import datetime
import pytz
from geo_utils import formato_gms_con_hemisferio

def render_inspector(latest, geo_data):
    if not latest:
        st.warning("⚠️ No hay fotos registradas en la base de datos.")
        return

    st.subheader("🔍 Inspector de estado")

    # Fecha última verificación
    colombia = pytz.timezone("America/Bogota")
    checked_at = latest.get("checked_at")
    if isinstance(checked_at, datetime):
        if checked_at.tzinfo is None:
            checked_at = checked_at.replace(tzinfo=pytz.UTC)
        checked_at_str = checked_at.astimezone(colombia).strftime("%d %b %y %H:%M")
    else:
        checked_at_str = "❌ No disponible"

    # GeoData
    if geo_data and "lat" in geo_data and "lon" in geo_data:
        lat = geo_data["lat"]
        lon = geo_data["lon"]
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
