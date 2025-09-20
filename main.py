# main.py
import streamlit as st
from datetime import datetime, timedelta
from checker import get_image_bytes, has_photo_changed
from db import save_photo, get_last_hash, get_last_photo_url
from notifier import send_whatsapp
from logs import log_access, get_access_logs

st.title("Photo Update")

# Inicializar estados streamlit
if "last_hash" not in st.session_state:
    st.session_state.last_hash = get_last_hash()
if "photo_url" not in st.session_state:
    st.session_state.photo_url = get_last_photo_url() or ""
if "notified_hash" not in st.session_state:
    st.session_state.notified_hash = None
if "last_checked" not in st.session_state:
    st.session_state.last_checked = datetime.min
if "access_logged" not in st.session_state:
    st.session_state.access_logged = False

# Mostrar miniatura Instagram guardada o pedir nueva URL si falla
image_bytes = get_image_bytes(st.session_state.photo_url) if st.session_state.photo_url else None
if image_bytes:
    st.image(image_bytes, caption="Miniatura actual")
else:
    st.warning("No se pudo cargar la miniatura desde la URL guardada.")
    nueva_url = st.text_input("Ingrese nueva URL de miniatura Instagram")
    if nueva_url and nueva_url != st.session_state.photo_url:
        st.session_state.photo_url = nueva_url
        st.info("URL actualizada. Por favor presiona 'Verificar actualización'")

# Pedir dirección opcional para ubicación (solo si no se registró antes)
direccion = st.text_input("Ingresa tu dirección para registro de acceso (opcional)")
if not st.session_state.access_logged:
    if direccion:
        log_access(address=direccion)
    else:
        log_access()
    st.session_state.access_logged = True

# Mostrar historial de accesos
st.subheader("Historial de accesos")
logs = get_access_logs(limit=10)
for log in logs:
    fecha = log.get("fecha").strftime("%Y-%m-%d %H:%M:%S")
    lat = log.get("latitud", "N/D")
    lon = log.get("longitud", "N/D")
    direccion = log.get("direccion") or ""
    st.write(f"{fecha} - {direccion} - Lat: {lat} - Lon: {lon}")

# Botón para verificar actualización de foto
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

# Mostrar última fecha de verificación
if st.session_state.last_checked > datetime.min:
    st.write(f"Última verificación: {st.session_state.last_checked.strftime('%Y-%m-%d %H:%M:%S')}")
