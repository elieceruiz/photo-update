# main.py
# ==============================
# Importaciones
# ==============================
import streamlit as st
from geolocation import handle_geolocation
from db import get_latest_record, get_access_logs

# Secciones modulares
from sections.inspector import show_latest_record
from sections.controls import handle_url_input
from sections.history import show_access_logs
from sections.display import show_image, manual_verification

# ==============================
# Configuración de la app
# ==============================
st.set_page_config(page_title="📸 Update", layout="centered")

# Inicializar session_state
if "geo_data" not in st.session_state or st.session_state.geo_data is None:
    st.session_state.geo_data = None
if "show_input" not in st.session_state:
    st.session_state.show_input = False
if "access_logged" not in st.session_state:
    st.session_state.access_logged = False

st.title("📸 Update")

# ==============================
# Cargar ubicación y último registro
# ==============================
with st.spinner("Cargando ubicación y datos, por favor espere..."):
    handle_geolocation(st.session_state)
    latest = get_latest_record()

# ==============================
# Mostrar inspector del último registro
# ==============================
if latest:
    show_latest_record(latest, st.session_state.geo_data)

# ==============================
# Manejar input de URL (primer registro o actualización)
# ==============================
nuevo_guardado = handle_url_input(latest, st.session_state.geo_data)

# ==============================
# Mostrar imagen actual
# ==============================
url_mongo = latest.get("photo_url") if latest else None
show_image(url_mongo, nuevo_guardado)

# ==============================
# Verificación manual
# ==============================
manual_verification()

# ==============================
# Mostrar historial de accesos
# ==============================
logs = get_access_logs()
show_access_logs(logs)
