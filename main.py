import streamlit as st
from checker import get_current_profile_pic_url, has_photo_changed
from notifier import send_whatsapp
from db import save_photo, get_collection
from time import sleep

st.title("Photo Update Notifier")

INSTAGRAM_URL = st.secrets["instagram"]["url"]

# Guardar el último hash de la foto en sesión
if "last_hash" not in st.session_state:
    st.session_state.last_hash = None

# Tiempo entre revisiones (segundos)
CHECK_INTERVAL = 60  # por ejemplo, 1 minuto

# Obtener URL de la foto actual
current_url = get_current_profile_pic_url(INSTAGRAM_URL)

if current_url:
    st.image(current_url, caption="Última foto detectada")

    # Chequear si la foto cambió usando hash
    changed, new_hash = has_photo_changed(current_url, st.session_state.last_hash)

    if changed:
        st.session_state.last_hash = new_hash
        sid = send_whatsapp(f"📸 Nueva foto detectada: {current_url}")
        st.success(f"Notificación enviada! SID: {sid}")
        save_photo(current_url)
else:
    st.error("No se pudo obtener la foto de perfil")

# Auto-revisión: esperar y recargar App
sleep(CHECK_INTERVAL)
st.rerun()
