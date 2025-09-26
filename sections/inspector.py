import streamlit as st
import pytz
from datetime import datetime
import hashlib
from urllib.parse import urlparse, parse_qs
from geo_utils import formato_gms_con_hemisferio

# ---------------------------
# Funciones para inspección
# ---------------------------

def show_latest_record(latest, geo_data):
    """
    Muestra en Streamlit el estado del último registro de foto.
    - latest: dict con información del último registro en Mongo
    - geo_data: dict con datos de geolocalización actuales
    """
    colombia = pytz.timezone("America/Bogota")

    # Procesar fecha de la última verificación
    checked_at = latest.get("checked_at")
    if isinstance(checked_at, datetime):
        if checked_at.tzinfo is None:
            checked_at = checked_at.replace(tzinfo=pytz.UTC)
        checked_at_str = checked_at.astimezone(colombia).strftime("%d %b %y %H:%M")
    else:
        checked_at_str = "❌ No disponible"

    # Procesar coordenadas y formato GMS
    if geo_data and "lat" in geo_data and "lon" in geo_data:
        lat = geo_data["lat"]
        lon = geo_data["lon"]
        lat_gms_str, lon_gms_str = formato_gms_con_hemisferio(lat, lon)
    else:
        lat = lon = None
        lat_gms_str = lon_gms_str = None

    # Mostrar JSON con estado actual
    st.subheader("🔍 Inspector de estado")
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


def show_debug(url, geo_data):
    """
    Muestra información de debug de un URL nuevo.
    - url: string del URL ingresado
    - geo_data: dict con geolocalización
    Devuelve el hash SHA256 del URL.
    """
    hash_value = hashlib.sha256(url.encode()).hexdigest()
    st.subheader("🛠️ Inspector DEBUG")
    st.json({
        "URL": url,
        "Hash generado": hash_value,
        "Fecha (UTC)": datetime.utcnow().strftime("%d %b %y %H:%M"),
        "Geo Data": geo_data if geo_data else "❌ No detectada"
    })
    return hash_value


def compare_urls(url_mongo, nuevo_url):
    """
    Compara el URL actual en Mongo con un URL nuevo y muestra diferencias en parámetros.
    """
    from streamlit import markdown, info, error
    if url_mongo:
        error("❌ El link en Mongo es DIFERENTE al nuevo")
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
            markdown("🔍 **Diferencias encontradas:**")
            for clave, val_mongo, val_nuevo in diferencias:
                markdown(f"- {clave} = {val_mongo}  (Mongo)")
                markdown(f"+ {clave} = {val_nuevo}  (Nuevo)")
        else:
            info("ℹ️ No se encontraron diferencias en los parámetros. Puede que cambie solo la parte base del link.")
