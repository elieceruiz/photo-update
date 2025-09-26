# main.py
# ==============================
# Importaciones
# ==============================
import streamlit as st
from datetime import datetime
import pytz
import pandas as pd
import hashlib
from urllib.parse import urlparse, parse_qs

# Módulos locales
from geolocation import handle_geolocation
from photo_checker import check_and_update_photo, download_image
from db import get_latest_record, get_access_logs, insert_photo_record
from geo_utils import formato_gms_con_hemisferio

# ==============================
# Configuración inicial
# ==============================
st.set_page_config(page_title="📸 Update", layout="centered")
colombia = pytz.timezone("America/Bogota")

# Variables en sesión para estado
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
# Si hay registro previo en Mongo
# ==============================
if latest:
    st.subheader("🔍 Inspector de estado")

    # Fecha de verificación → formateada en hora local Bogotá
    checked_at = latest.get("checked_at")
    if isinstance(checked_at, datetime):
        if checked_at.tzinfo is None:  # naive → asumimos UTC
            checked_at = checked_at.replace(tzinfo=pytz.UTC)
        checked_at_str = checked_at.astimezone(colombia).strftime("%d %b %y %H:%M")
    else:
        checked_at_str = "❌ No disponible"

    # GeoData actual de sesión
    if st.session_state.geo_data and "lat" in st.session_state.geo_data and "lon" in st.session_state.geo_data:
        lat = st.session_state.geo_data["lat"]
        lon = st.session_state.geo_data["lon"]
        lat_gms_str, lon_gms_str = formato_gms_con_hemisferio(lat, lon)
    else:
        lat = lon = None
        lat_gms_str = lon_gms_str = None

    # Inspector de estado (últimos valores)
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
    # Comparación de URLs
    # ==============================
    url_mongo = latest.get("photo_url", "")

    st.subheader("🧾 Comparación de URLs")
    st.write("🔗 URL en Mongo:")
    st.code(url_mongo if url_mongo else "❌ No registrada", language="text")

    # Input para nuevo URL
    nuevo_url = st.text_input("✏️ Ingresa nuevo enlace para comparar y registrar")

    if nuevo_url:
        if url_mongo == nuevo_url:
            st.success("✅ El link en Mongo es IGUAL al nuevo")
        else:
            st.error("❌ El link en Mongo es DIFERENTE al nuevo")

            # Comparación de parámetros de query
            mongo_params = parse_qs(urlparse(url_mongo).query) if url_mongo else {}
            nuevo_params = parse_qs(urlparse(nuevo_url).query)
            todas_claves = set(mongo_params.keys()) | set(nuevo_params.keys())

            st.markdown("🔍 **Diferencias encontradas por parámetro:**")
            diferencias = False
            for clave in todas_claves:
                val_mongo = mongo_params.get(clave, ["-"])[0]
                val_nuevo = nuevo_params.get(clave, ["-"])[0]
                if val_mongo != val_nuevo:
                    diferencias = True
                    st.markdown(f"- {clave} = {val_mongo}  (Mongo)")
                    st.markdown(f"+ {clave} = {val_nuevo}  (Nuevo)")

            if not diferencias:
                st.info("ℹ️ No se encontraron diferencias en los parámetros. Puede que cambie solo la parte base del link.")

            # ==============================
            # Inspector DEBUG antes de guardar
            # ==============================
            st.subheader("🛠️ Inspector DEBUG")
            hash_value = hashlib.sha256(nuevo_url.encode()).hexdigest()
            st.json({
                "Nuevo URL": nuevo_url,
                "Hash generado": hash_value,
                "Fecha (UTC)": datetime.utcnow().strftime("%d %b %y %H:%M"),
                "Geo Data": st.session_state.geo_data if st.session_state.geo_data else "❌ No detectada"
            })

            # Guardar nuevo registro en Mongo
            try:
                insert_photo_record(
                    photo_url=nuevo_url,
                    hash_value=hash_value,
                    checked_at=datetime.utcnow().replace(tzinfo=pytz.UTC),
                    geo_data=st.session_state.geo_data
                )
                st.success("✅ Nuevo enlace guardado en Mongo con hash, fecha (UTC) y ubicación")
            except Exception as e:
                st.error(f"💥 Error en insert_photo_record: {e}")

    # ==============================
    # Mostrar imagen actual
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
# Si NO hay registros previos
# ==============================
else:
    st.warning("⚠️ No hay fotos registradas en la base de datos.")
    nuevo_url = st.text_input("✏️ Registrar primer URL de foto")
    if nuevo_url:
        hash_value = hashlib.sha256(nuevo_url.encode()).hexdigest()

        # Inspector DEBUG inicial
        st.subheader("🛠️ Inspector DEBUG")
        st.json({
            "Primer URL": nuevo_url,
            "Hash generado": hash_value,
            "Fecha (UTC)": datetime.utcnow().strftime("%d %b %y %H:%M"),
            "Geo Data": st.session_state.geo_data if st.session_state.geo_data else "❌ No detectada"
        })

        # Guardar primer registro en Mongo
        try:
            insert_photo_record(
                photo_url=nuevo_url,
                hash_value=hash_value,
                checked_at=datetime.utcnow().replace(tzinfo=pytz.UTC),
                geo_data=st.session_state.geo_data
            )
            st.success("✅ Primer enlace guardado en Mongo con hash, fecha (UTC) y ubicación")
        except Exception as e:
            st.error(f"💥 Error en insert_photo_record: {e}")

# ==============================
# Botón de verificación manual
# ==============================
if st.button("🔄 Verificar foto ahora"):
    changed, msg = check_and_update_photo()
    if changed:
        st.success(msg)
    else:
        st.info(msg)

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