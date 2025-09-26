# sections/inspector.py
import streamlit as st
from geo_utils import formato_gms_con_hemisferio
from datetime import datetime
import hashlib
from urllib.parse import urlparse, parse_qs

# ---------------------------
# Funciones para inspección
# ---------------------------

def show_latest_record(latest, geo_data):
    """
    Muestra el estado del último registro de foto de forma legible.
    - latest: dict con información del último registro en Mongo
    - geo_data: dict con datos de geolocalización actuales
    """
    colombia = st.session_state.get("timezone", None) or None

    # Fecha última verificación
    checked_at = latest.get("checked_at")
    if isinstance(checked_at, datetime):
        if checked_at.tzinfo is None:
            checked_at = checked_at.replace(tzinfo=None)
        checked_at_str = checked_at.strftime("%d %b %y %H:%M")
    else:
        checked_at_str = "No disponible"

    # Hash
    hash_value = latest.get("hash") or latest.get("hash_value", "No disponible")

    # Ubicación
    if geo_data and "lat" in geo_data and "lon" in geo_data:
        lat = geo_data["lat"]
        lon = geo_data["lon"]
        lat_gms, lon_gms = formato_gms_con_hemisferio(lat, lon)
    else:
        lat = lon = lat_gms = lon_gms = "No detectada"

    # Mostrar información legible
    st.subheader("🔍 Estado del último registro")
    st.markdown(f"**Último Hash:** {hash_value}")
    st.markdown(f"**Última verificación:** {checked_at_str}")
    st.markdown("**Ubicación actual:**")
    st.markdown(f"- Decimal: lat {lat}, lon {lon}")
    st.markdown(f"- GMS: lat {lat_gms}, lon {lon_gms}")


def show_debug(url, geo_data):
    """
    Muestra información de debug de un URL nuevo de forma legible.
    Devuelve el hash SHA256 del URL.
    """
    hash_value = hashlib.sha256(url.encode()).hexdigest()
    st.subheader("🛠️ Inspector DEBUG")
    st.markdown(f"- **URL:** {url}")
    st.markdown(f"- **Hash generado:** {hash_value}")
    st.markdown(f"- **Fecha (UTC):** {datetime.utcnow().strftime('%d %b %y %H:%M')}")
    if geo_data:
        lat = geo_data.get("lat", "No detectada")
        lon = geo_data.get("lon", "No detectada")
        acc = geo_data.get("accuracy", "?")
        st.markdown(f"- **Geo Data:** lat {lat}, lon {lon}, ±{acc} m")
    else:
        st.markdown("- **Geo Data:** No detectada")
    return hash_value


def compare_urls(url_mongo, nuevo_url):
    """
    Compara el URL actual en Mongo con un URL nuevo y muestra diferencias en parámetros.
    """
    if url_mongo:
        st.error("❌ El link en Mongo es DIFERENTE al nuevo")
        mongo_params = parse_qs(urlparse(url_mongo).query)
        nuevo_params = parse_qs(urlparse(nuevo_url).query)
        todas_claves = set(mongo_params.keys()) | set(nuevo_params.keys())

        diferencias = []
        for clave in todas_claves:
            val_mongo = mongo_params.get(clave, ["-"])[0]
            val_nuevo = nuevo_params.get(clave, ["-"])[0]
            if val_mongo != val_nuevo:
                diferencias.append((clave, val_mongo, val_nuevo))

        if diferencias:
            st.markdown("🔍 **Diferencias encontradas:**")
            for clave, val_mongo, val_nuevo in diferencias:
                st.markdown(f"- {clave} = {val_mongo}  (Mongo)")
                st.markdown(f"+ {clave} = {val_nuevo}  (Nuevo)")
        else:
            st.info("ℹ️ No se encontraron diferencias en los parámetros. Puede que cambie solo la parte base del link.")
