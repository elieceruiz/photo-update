# main.py
# ==============================
# Importaciones
# ==============================
import streamlit as st
from datetime import datetime
import pytz
import pandas as pd
import hashlib  # 👈 para generar hash
from urllib.parse import urlparse, parse_qs

# Módulos locales
from geolocation import handle_geolocation
from photo_checker import check_and_update_photo, download_image
from db import get_latest_record, get_access_logs, insert_photo_record  # 👈 nuevo import
from geo_utils import formato_gms_con_hemisferio

# ==============================
# Configuración inicial
# ==============================
st.set_page_config(page_title="📸 Update", layout="centered")
colombia = pytz.timezone("America/Bogota")

if "access_logged" not in st.session_state:
    st.session_state.access_logged = False
if "geo_data" not in st.session_state or st.session_state.geo_data is None:
    st.session_state.geo_data = None

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
# Si hay registro
# ==============================
if latest:
    st.subheader("🔍 Inspector de estado")

    checked_at = latest.get("checked_at")
    if isinstance(checked_at, datetime):
        if checked_at.tzinfo is None:
            checked_at = checked_at.replace(tzinfo=pytz.UTC)
        checked_at = checked_at.astimezone(colombia).strftime("%d %b %y %H:%M")

    if st.session_state.geo_data and "lat" in st.session_state.geo_data and "lon" in st.session_state.geo_data:
        lat = st.session_state.geo_data["lat"]
        lon = st.session_state.geo_data["lon"]
        lat_gms_str, lon_gms_str = formato_gms_con_hemisferio(lat, lon)
    else:
        lat = lon = None
        lat_gms_str = lon_gms_str = None

    st.json({
        "Último Hash": latest.get("hash"),
        "Última verificación": checked_at or "Nunca",
        "Ubicación": {
            "decimal": {
                "lat": lat if lat is not None else "No detectada",
                "lon": lon if lon is not None else "No detectada",
            },
            "GMS": {
                "lat": lat_gms_str if lat_gms_str is not None else "No detectada",
                "lon": lon_gms_str if lon_gms_str is not None else "No detectada",
            }
        }
    })

    # ==============================
    # Comparación de URLs
    # ==============================
    url_mongo = latest.get("photo_url", "")
    url_manual = "https://instagram.feoh4-3.fna.fbcdn.net/..."  # 👈 tu URL manual

    st.subheader("🧾 Comparación de URLs")
    st.write("🔗 URL en Mongo:")
    st.code(url_mongo, language="text")
    st.write("🔗 URL manual:")
    st.code(url_manual, language="text")

    if url_mongo == url_manual:
        st.success("✅ El link en Mongo es IGUAL al manual")
    else:
        st.error("❌ El link en Mongo es DIFERENTE al manual")

        # Comparación detallada
        mongo_params = parse_qs(urlparse(url_mongo).query)
        manual_params = parse_qs(urlparse(url_manual).query)
        todas_claves = set(mongo_params.keys()) | set(manual_params.keys())

        st.markdown("🔍 **Diferencias encontradas por parámetro:**")
        diferencias = False
        for clave in todas_claves:
            val_mongo = mongo_params.get(clave, ["-"])[0]
            val_manual = manual_params.get(clave, ["-"])[0]
            if val_mongo != val_manual:
                diferencias = True
                st.markdown(f"- {clave} = {val_mongo}  (Mongo)")
                st.markdown(f"+ {clave} = {val_manual}  (Manual)")

        if not diferencias:
            st.info("ℹ️ No se encontraron diferencias en los parámetros. Puede que cambie solo la parte base del link.")

        # ==============================
        # Campo para ingresar nuevo link
        # ==============================
        nuevo_url = st.text_input("✏️ Ingresar nuevo enlace válido")
        if nuevo_url:
            hash_value = hashlib.sha256(nuevo_url.encode()).hexdigest()
            insert_photo_record(nuevo_url, hash_value)
            st.success("✅ Nuevo enlace guardado en Mongo con hash generado")

    # ==============================
    # Mostrar imagen
    # ==============================
    try:
        img_bytes = download_image(url_mongo)
        if img_bytes:
            st.image(img_bytes, caption="Miniatura actual")
        else:
            st.error("❌ No se pudo cargar la imagen")
    except Exception as e:
        st.error(f"❌ Error: {e}")

# ==============================
# Si NO hay registros
# ==============================
else:
    st.warning("⚠️ No hay fotos registradas en la base de datos.")
    nuevo_url = st.text_input("✏️ Registrar primer URL de foto")
    if nuevo_url:
        hash_value = hashlib.sha256(nuevo_url.encode()).hexdigest()
        insert_photo_record(nuevo_url, hash_value)
        st.success("✅ Primer enlace guardado en Mongo con hash generado")

# ==============================
# Botón verificación manual
# ==============================
if st.button("🔄 Verificar foto ahora"):
    changed, msg = check_and_update_photo()
    if changed:
        st.success(msg)
    else:
        st.info(msg)

# ==============================
# Historial accesos
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