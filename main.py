# main.py
import streamlit as st
from datetime import datetime, timedelta
from checker import get_image_bytes, has_photo_changed
from db import save_photo, get_last_hash, get_last_photo_url
from notifier import send_whatsapp
from logs import log_access, get_access_logs
from streamlit_geolocation import streamlit_geolocation
import pandas as pd

st.title("Photo Update con Detección Controlada de Ubicación")

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
if "detecting_location" not in st.session_state:
    st.session_state.detecting_location = False
if "location" not in st.session_state:
    st.session_state.location = None

# Mostrar miniatura
image_bytes = get_image_bytes(st.session_state.photo_url) if st.session_state.photo_url else None
if image_bytes:
    st.image(image_bytes, caption="Miniatura actual")
else:
    st.warning("No se pudo cargar la miniatura desde la URL guardada.")

    nueva_url = st.text_input("Ingrese nueva URL de miniatura Instagram")
    if nueva_url and nueva_url != st.session_state.photo_url:
        st.session_state.photo_url = nueva_url
        st.info("URL actualizada. Por favor presiona 'Verificar actualización'")

# Detectar ubicación y registrar acceso con spinner
if not st.session_state.access_logged:
    if st.button("Detectar mi ubicación y registrar acceso"):
        st.session_state.detecting_location = True

    if st.session_state.detecting_location:
        with st.spinner("Obteniendo ubicación, por favor espera..."):
            location = streamlit_geolocation()
            if location:
                st.session_state.location = location
                lat = location.get("latitude")
                lon = location.get("longitude")
                st.success(f"Ubicación detectada: latitud {lat}, longitud {lon}")
                log_access(lat=lat, lon=lon)
                st.session_state.access_logged = True
                st.session_state.detecting_location = False
            else:
                st.error("No se pudo obtener la ubicación o permiso denegado.")
                st.session_state.detecting_location = False

# Mostrar historial
st.subheader("Historial de accesos")
logs = get_access_logs(limit=10)
data = []
for log in logs:
    fecha = log.get("fecha").strftime("%Y-%m-%d %H:%M:%S")
    lat = log.get("latitud")
    lon = log.get("longitud")
    data.append({"Fecha": fecha, "Latitud": lat, "Longitud": lon})

df_logs = pd.DataFrame(data)
st.dataframe(df_logs)

# Verificar cambios en la foto
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

if st.session_state.last_checked > datetime.min:
    st.write(f"Última verificación: {st.session_state.last_checked.strftime('%Y-%m-%d %H:%M:%S')}")
