import streamlit as st
import requests
import hashlib
from db import save_photo
from notifier import send_whatsapp
from streamlit_autorefresh import st_autorefresh

st.title("Photo Update Notifier (cuenta privada)")

# URL de la miniatura pública de la cuenta privada
INSTAGRAM_MINIATURE_URL = "https://instagram.feoh4-3.fna.fbcdn.net/v/t51.2885-19/548878794_18524321074061703_2757381932676116877_n.jpg?..."

# Guardar el último hash en sesión
if "last_hash" not in st.session_state:
    st.session_state.last_hash = None

# Funciones
def get_image_bytes(url: str) -> bytes:
    r = requests.get(url)
    return r.content if r.status_code == 200 else None

def hash_image(image_bytes: bytes) -> str:
    return hashlib.sha256(image_bytes).hexdigest()

# Auto refresco cada minuto
st_autorefresh(interval=60 * 1000, key="refresh")

# Mostrar miniatura actual
st.image(INSTAGRAM_MINIATURE_URL, caption="Miniatura actual")

# Descargar y calcular hash
image_bytes = get_image_bytes(INSTAGRAM_MINIATURE_URL)
if image_bytes:
    current_hash = hash_image(image_bytes)
    if st.session_state.last_hash != current_hash:
        st.session_state.last_hash = current_hash
        st.session_state.last_hash = current_hash

        # Guardar en MongoDB
        save_photo(INSTAGRAM_MINIATURE_URL)

        # Notificar por WhatsApp
        try:
            sid = send_whatsapp(f"📸 Nueva foto detectada: {INSTAGRAM_MINIATURE_URL}")
            st.success(f"Notificación enviada! SID: {sid}")
        except Exception as e:
            st.error(f"No se pudo enviar la notificación: {e}")
    else:
        st.info("No hay cambios en la foto.")
else:
    st.error("No se pudo descargar la miniatura.")
