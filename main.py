# main.py
import streamlit as st
from checker import get_image_bytes, hash_image, has_photo_changed
from db import save_photo, get_last_hash
from notifier import send_whatsapp
from streamlit_autorefresh import st_autorefresh

st.title("Photo Update")

INSTAGRAM_MINIATURE_URL = "https://instagram.feoh4-3.fna.fbcdn.net/v/t51.2885-19/548878794_18524321074061703_2757381932676116877_n.jpg?stp=dst-jpg_s150x150_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLmRqYW5nby43MjguYzIifQ&_nc_ht=instagram.feoh4-3.fna.fbcdn.net&_nc_cat=103&_nc_oc=Q6cZ2QHC2hxRsKhT75OwVtO4Oc9RmvK_fmSXw_o9ny7J6GUk3on0m_ofsXcFK-WzMSUVEV0-Hi6H4wGNVOcXpVODNynY&_nc_ohc=mO3tE2y20x8Q7kNvwEvIxLs&_nc_gid=bzqjWzuarJVxkX7UWq6JNA&edm=AOQ1c0wBAAAA&ccb=7-5&oh=00_AfY6hM6ogTVzUIvQ3WpDLUNs4jg5EUle9618OVX509MsYg&oe=68D4B419&_nc_sid=8b3546"

# Obtener hash guardado al iniciar si no hay hash en sesión
if "last_hash" not in st.session_state:
    st.session_state.last_hash = get_last_hash()

# Control para activar o desactivar autorefresh
auto_refresh = st.checkbox("Autorefresh cada minuto", value=False)

if auto_refresh:
    st_autorefresh(interval=60 * 1000, key="refresh")

st.image(INSTAGRAM_MINIATURE_URL, caption="Miniatura actual")

changed, current_hash = has_photo_changed(INSTAGRAM_MINIATURE_URL, st.session_state.last_hash)

if changed:
    st.session_state.last_hash = current_hash
    save_photo(INSTAGRAM_MINIATURE_URL, current_hash)

    try:
        sid = send_whatsapp(f"📸 Nueva foto detectada: {INSTAGRAM_MINIATURE_URL}")
        st.success(f"Notificación enviada! SID: {sid}")
    except Exception as e:
        st.error(f"No se pudo enviar la notificación: {e}")
else:
    st.info("No hay cambios en la foto.")
