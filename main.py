import streamlit as st
from geolocation import handle_geolocation
from photo_checker import check_and_update_photo, download_image
from db import get_latest_record, get_access_logs

from sections.inspector import show_latest_record
from sections.controls import handle_url_input
from sections.history import show_access_logs

# ---------------------------
# Configuración de la app
# ---------------------------
st.set_page_config(page_title="📸 Update", layout="centered")

# Inicializar session_state
if "geo_data" not in st.session_state or st.session_state.geo_data is None:
    st.session_state.geo_data = None
if "show_input" not in st.session_state:
    st.session_state.show_input = False
if "access_logged" not in st.session_state:
    st.session_state.access_logged = False

st.title("📸 Update")

# ---------------------------
# Cargar ubicación y último registro
# ---------------------------
with st.spinner("Cargando ubicación y datos, por favor espere..."):
    handle_geolocation(st.session_state)
    latest = get_latest_record()

# ---------------------------
# Mostrar inspector del último registro
# ---------------------------
if latest:
    show_latest_record(latest, st.session_state.geo_data)

# ---------------------------
# Manejar input de URL (primer registro o actualización)
# ---------------------------
nuevo_guardado = handle_url_input(latest, st.session_state.geo_data)

# ---------------------------
# Mostrar imagen actual
# ---------------------------
url_mongo = latest.get("photo_url") if latest else None
try:
    if url_mongo:
        img_bytes = download_image(url_mongo)
        if img_bytes:
            st.image(img_bytes, caption="Miniatura actual")
        else:
            st.error("❌ No se pudo cargar la imagen")
    elif not latest and not nuevo_guardado:
        st.warning("⚠️ No hay fotos registradas en la base de datos.")
except Exception as e:
    st.error(f"❌ Error: {e}")

# ---------------------------
# Verificación manual de foto
# ---------------------------
if st.button("🔄 Verificar foto ahora"):
    changed, msg = check_and_update_photo()
    st.session_state.show_input = changed
    if changed:
        st.success(msg)
    else:
        st.info(msg)

# ---------------------------
# Mostrar historial de accesos
# ---------------------------
logs = get_access_logs()
show_access_logs(logs)
