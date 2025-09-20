import streamlit as st
from checker import get_current_profile_pic_url
from notifier import send_whatsapp
from db import save_photo, get_collection

st.title("Photo Update Notifier")

INSTAGRAM_URL = st.secrets["instagram"]["url"]

# Guardar la última foto en sesión
if "last_photo" not in st.session_state:
    st.session_state.last_photo = None

current_photo = get_current_profile_pic_url(INSTAGRAM_URL)

if current_photo:
    st.image(current_photo, caption="Última foto detectada")

    if st.session_state.last_photo != current_photo:
        st.session_state.last_photo = current_photo
        sid = send_whatsapp(f"📸 Nueva foto detectada: {current_photo}")
        st.success(f"Notificación enviada! SID: {sid}")
        save_photo(current_photo)  # guarda en MongoDB
else:
    st.error("No se pudo obtener la foto de perfil")
