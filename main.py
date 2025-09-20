# main.py
import streamlit as st
from checker import get_image_bytes, hash_image, has_photo_changed
from db import save_photo
from notifier import send_whatsapp
from streamlit_autorefresh import st_autorefresh

st.title("Photo Update Notifier (cuenta privada)")

# Miniatura pública de la cuenta privada
INSTAGRAM_MINIATURE_URL = "https://instagram.feoh4-3.fna.fbcdn.net/v/t51.2885-19/548878794_18524321074061703_2757381932676116877_n.jpg?..."

# Guardar último hash en sesión
if "last_hash" not in st.session_state:
    st.session_state.last_hash = None

# Auto refresco cada minuto
st_autorefresh(interval=60 * 1000, key="refresh")

# Mostrar la miniatura
st.image(INSTAGRAM_MINIATURE_URL, caption="Miniatura actual")

# Detectar cambios
changed, current_hash = has_photo_changed(INSTAGRAM_MINIATURE_URL, st.session_state.last_hash)

if changed:
    st.session_state.last_hash = current_hash
    save_photo(INSTAGRAM_MINIATURE_URL)
    
    try:
        sid = send_whatsapp(f"📸 Nueva foto detectada: {INSTAGRAM_MINIATURE_URL}")
        st.success(f"Notificación enviada! SID: {sid}")
    except Exception as e:
        st.error(f"No se pudo enviar la notificación: {e}")
else:
    st.info("No hay cambios en la foto.")
