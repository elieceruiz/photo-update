# main.py
import streamlit as st
from datetime import datetime, timedelta
from checker import get_image_bytes, has_photo_changed
from db import save_photo, get_last_hash, get_last_photo_url
from notifier import send_whatsapp

st.title("Photo Update")

# Cargar último hash y URL
if "last_hash" not in st.session_state:
    st.session_state.last_hash = get_last_hash()
if "photo_url" not in st.session_state:
    st.session_state.photo_url = get_last_photo_url() or ""
if "notified_hash" not in st.session_state:
    st.session_state.notified_hash = None
if "last_checked" not in st.session_state:
    st.session_state.last_checked = datetime.min

# Intentar cargar la imagen desde la URL guardada
image_bytes = get_image_bytes(st.session_state.photo_url) if st.session_state.photo_url else None
if image_bytes:
    st.image(image_bytes, caption="Miniatura actual")
else:
    st.warning("No se pudo cargar la miniatura desde la URL guardada.")
    nueva_url = st.text_input("Ingrese nueva URL de miniatura Instagram")
    if nueva_url and nueva_url != st.session_state.photo_url:
        st.session_state.photo_url = nueva_url
        st.info("URL actualizada. Por favor presiona 'Verificar actualización'")

# Botón para verificar actualización y evitar consultas frecuentes
min_interval = timedelta(minutes=10)
if st.button("Verificar actualización"):
    now = datetime.now()
    if now - st.session_state.last_checked < min_interval:
        st.warning(f"Por favor espera {int(min_interval.total_seconds()/60)} minutos entre chequeos.")
    else:
        st.session_state.last_checked = now
        changed, current_hash = has_photo_changed(st.session_state.photo_url, st.session_state.last_hash)
        if changed and st.session_state.notified_hash != current_hash:
            st.session_state.last_hash = current_hash
            st.session_state.notified_hash = current_hash
            save_photo(st.session_state.photo_url, current_hash)
            try:
                sid = send_whatsapp(f"📸 Nueva foto detectada: {st.session_state.photo_url}")
                st.success(f"Notificación enviada! SID: {sid}")
            except Exception as e:
                st.error(f"No se pudo enviar la notificación: {e}")
        else:
            st.info("No hay cambios en la foto o ya se notificó esta imagen.")

# Mostrar última verificación
if st.session_state.last_checked > datetime.min:
    st.write(f"Última verificación: {st.session_state.last_checked.strftime('%Y-%m-%d %H:%M:%S')}")
