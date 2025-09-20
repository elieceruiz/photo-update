# main.py
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
from checker import get_image_bytes, has_photo_changed
from db import save_photo, get_last_hash, get_last_photo_url, seed_initial_photo
from notifier import send_whatsapp
from logs import log_access, get_access_logs
from streamlit_geolocation import streamlit_geolocation

st.set_page_config(page_title="Photo Update", layout="centered")
st.title("📸 Photo Update")

# Semilla inicial si DB está vacía
seed_initial_photo()

# Inicializar estados
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

# Detecta ubicación y registra acceso
if not st.session_state.access_logged:
    with st.spinner("Detectando ubicación automáticamente, espere..."):
        location = streamlit_geolocation()
        if location:
            lat = location.get("latitude")
            lon = location.get("longitude")
            st.success(f"Ubicación detectada: lat {lat}, lon {lon}")
            log_access(lat=lat, lon=lon)
            st.session_state.access_logged = True
        else:
            st.warning("⚠️ No se pudo obtener la ubicación (permiso denegado).")
            log_access(lat=None, lon=None)
            st.session_state.access_logged = True

# Inspector bonito
st.subheader("🔍 Inspector de estado")
col1, col2 = st.columns(2)
with col1:
    st.metric("Último Hash", st.session_state.last_hash or "Ninguno")
with col2:
    last_time = (st.session_state.last_checked.strftime('%Y-%m-%d %H:%M:%S') 
                 if st.session_state.last_checked > datetime.min else "Nunca")
    st.metric("Última verificación", last_time)

# Mostrar miniatura Instagram
image_bytes = get_image_bytes(st.session_state.photo_url) if st.session_state.photo_url else None
if image_bytes:
    st.image(image_bytes, caption="Miniatura actual", width=200)
else:
    st.warning("No se pudo cargar la miniatura desde la URL guardada.")
    nueva_url = st.text_input("📎 Ingrese nueva URL de miniatura Instagram")
    if nueva_url and nueva_url != st.session_state.photo_url:
        st.session_state.photo_url = nueva_url
        st.info("URL actualizada. Presiona 'Verificar actualización'.")

# Mostrar historial de accesos
st.subheader("📍 Historial de accesos recientes")
logs = get_access_logs(limit=10)
data = []
for log in logs:
    fecha = log.get("fecha").strftime("%Y-%m-%d %H:%M:%S")
    lat = log.get("latitud")
    lon = log.get("longitud")
    data.append({"Fecha": fecha, "Latitud": lat, "Longitud": lon})

df_logs = pd.DataFrame(data)
st.dataframe(df_logs, use_container_width=True)

# Botón para verificar cambios en la foto
st.subheader("🔄 Verificación de cambios")
min_interval = timedelta(minutes=10)
if st.button("Verificar actualización"):
    now = datetime.now()
    if now - st.session_state.last_checked < min_interval:
        st.warning(f"⏳ Espera {int(min_interval.total_seconds()/60)} minutos entre chequeos.")
    else:
        st.session_state.last_checked = now
        changed, current_hash = has_photo_changed(st.session_state.photo_url, st.session_state.last_hash)
        if changed and st.session_state.notified_hash != current_hash:
            st.session_state.last_hash = current_hash
            st.session_state.notified_hash = current_hash
            if save_photo(st.session_state.photo_url, current_hash):
                try:
                    sid = send_whatsapp(f"📸 Nueva foto detectada: {st.session_state.photo_url}")
                    st.success(f"✅ Notificación enviada! SID: {sid}")
                except Exception as e:
                    st.error(f"No se pudo enviar la notificación: {e}")
            else:
                st.info("⚠️ Foto ya estaba registrada, no se guardó duplicado.")
        else:
            st.info("No hay cambios en la foto o ya se notificó esta imagen.")
