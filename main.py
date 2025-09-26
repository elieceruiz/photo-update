# ==============================
# Importaciones
# ==============================
import streamlit as st
from datetime import datetime
import pytz
import pandas as pd
import difflib

# Módulos locales que encapsulan lógica
from geolocation import handle_geolocation          # Detecta y guarda la ubicación
from photo_checker import check_and_update_photo, download_image  # Verifica cambios de foto y descarga
from db import get_latest_record, get_access_logs   # Acceso a la base de datos Mongo
from geo_utils import formato_gms_con_hemisferio    # Convierte coordenadas decimales a formato GMS

# ==============================
# Configuración inicial de la app
# ==============================
st.set_page_config(page_title="📸 Update", layout="centered")
colombia = pytz.timezone("America/Bogota")  # Zona horaria de referencia

# Inicializar variables de sesión si no existen
if "access_logged" not in st.session_state:
    st.session_state.access_logged = False
if "geo_data" not in st.session_state or st.session_state.geo_data is None:
    st.session_state.geo_data = None

# ==============================
# Título principal
# ==============================
st.title("📸 Update")

# ==============================
# Cargar datos iniciales
# ==============================
with st.spinner("Cargando ubicación y datos, por favor espere..."):
    handle_geolocation(st.session_state)   # Detectar ubicación
    latest = get_latest_record()           # Obtener último registro de MongoDB

# ==============================
# Bloque: si existe registro
# ==============================
if latest:
    st.subheader("🔍 Inspector de estado")

    # Procesar fecha de última verificación
    checked_at = latest.get("checked_at")
    if isinstance(checked_at, datetime):
        if checked_at.tzinfo is None:  # Si no tiene tz, forzar UTC
            checked_at = checked_at.replace(tzinfo=pytz.UTC)
        checked_at = checked_at.astimezone(colombia).strftime("%d %b %y %H:%M")

    # Procesar ubicación
    if st.session_state.geo_data and "lat" in st.session_state.geo_data and "lon" in st.session_state.geo_data:
        lat = st.session_state.geo_data["lat"]
        lon = st.session_state.geo_data["lon"]
        lat_gms_str, lon_gms_str = formato_gms_con_hemisferio(lat, lon)  # Pasar a formato GMS
    else:
        lat = lon = None
        lat_gms_str = lon_gms_str = None

    # Mostrar estado en JSON
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
    url_mongo = latest.get("photo_url", "")   # URL guardada en Mongo
    url_manual = "https://instagram.feoh4-3.fna.fbcdn.net/v/t51.2885-19/548878794_18524321074061703_2757381932676116877_n.jpg?stp=dst-jpg_s320x320_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLmRqYW5nby43MjguYzIifQ&_nc_ht=instagram.feoh4-3.fna.fbcdn.net&_nc_cat=103&_nc_oc=Q6cZ2QGrT_eK1VJqrn9l5kH3TQozgN3drJ3au4uPl9hCjQowBwmGjIqTUq6vTM1zmw1p1mwCkucnK_BooQSwTB3xDJRd&_nc_ohc=dNVSXWIH1CMQ7kNvwExP4l5&_nc_gid=iimf2mgnXbswpxNZ26RnTg&edm=AOQ1c0wBAAAA&ccb=7-5&oh=00_AfZkhVo5CSsxN6G0Tm0OKYrVTiH3nAyJmqDZpKoaEgTf6Q&oe=68DBBC19&_nc_sid=8b3546"

    st.subheader("🧾 Comparación de URLs")
    st.write("🔗 URL en Mongo:", url_mongo)
    st.write("🔗 URL manual:", url_manual)

    # Verificar igualdad
    if url_mongo == url_manual:
        st.success("✅ El link en Mongo es IGUAL al manual")
    else:
        st.error("❌ El link en Mongo es DIFERENTE al manual")

        # Generar diferencias carácter por carácter
        diff = difflib.ndiff(url_mongo, url_manual)

        st.write("🔍 Diferencias encontradas (resaltando cambios):")
        for d in diff:
            if d.startswith("-"):
                # Mostrar en negrita lo que estaba antes (Mongo)
                st.markdown(f"- **{d[2:]}** (estaba en Mongo)")
            elif d.startswith("+"):
                # Mostrar normal lo nuevo (Manual)
                st.markdown(f"+ {d[2:]} (nuevo en Manual)")

    # ==============================
    # Mostrar la imagen
    # ==============================
    try:
        img_bytes = download_image(url_mongo)   # Descarga la imagen de la URL en Mongo
        if img_bytes:
            st.image(img_bytes, caption="Miniatura actual")
        else:
            st.error("❌ No se pudo cargar la imagen")
    except Exception as e:
        st.error(f"❌ Error: {e}")

# ==============================
# Bloque: si NO hay registro
# ==============================
else:
    st.warning("⚠️ No hay fotos registradas en la base de datos.")

# ==============================
# Botón para verificar manualmente
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
    # Crear DataFrame con los accesos
    df = pd.DataFrame(data)
    df.index = range(1, len(df) + 1)
    df = df.iloc[::-1]  # Ordenar de más reciente a más antiguo
    st.subheader("📜 Historial de accesos")
    st.dataframe(df, use_container_width=True)