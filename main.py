# main.py
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
from checker import get_image_bytes, has_photo_changed, hash_image
from db import save_photo, get_last_hash, get_last_photo_url, get_history
from notifier import send_whatsapp
from logs import log_access, get_access_logs
from streamlit_geolocation import streamlit_geolocation

st.title("📸 Photo Update Tracker")

# === Inicializar estados ===
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

# === Detectar ubicación solo una vez ===
if not st.session_state.access_logged:
    with st.spinner("Detectando ubicación automáticamente, espere..."):
        location = streamlit_geolocation()
        if location:
            lat = location.get("latitude")
            lon = location.get("longitude")
            st.success(f"Ubicación detectada: latitud {lat}, longitud {lon}")
            log_access(lat=lat, lon=lon)
            st.session_state.access_logged = True
        else:
            st.error("No se pudo obtener la ubicación o permiso denegado.")

# === Mostrar miniatura actual ===
image_bytes = get_image_bytes(st.session_state.photo_url) if st.session_state.photo_url else None
if image_bytes:
    st.image(image_bytes, caption="Miniatura actual")
else:
    st.warning("No se pudo cargar la miniatura desde la URL guardada.")
    nueva_url = st.text_input("Ingrese nueva URL de miniatura Instagram")
    if nueva_url and nueva_url != st.session_state.photo_url:
        st.session_state.photo_url = nueva_url
        st.info("URL actualizada. Guardando en historial...")
        image_bytes = get_image_bytes(nueva_url)
        if image_bytes:
            hash_val = hash_image(image_bytes)
        else:
            hash_val = "manual_update"
        saved = save_photo(nueva_url, hash_val)
        if saved:
            st.success("Foto registrada en historial.")
            st.session_state.last_hash = hash_val
        else:
            st.info("La foto ya estaba registrada, no se duplicó.")

# === Historial de accesos ===
st.subheader("📍 Historial de accesos recientes")
logs = get_access_logs(limit=10)
data = []
for log in logs:
    fecha = log.get("fecha").strftime("%Y-%m-%d %H:%M:%S")
    lat = log.get("latitud")
    lon = log.get("longitud")
    data.append({"Fecha": fecha, "Latitud": lat, "Longitud": lon})

df_logs = pd.DataFrame(data)
st.dataframe(df_logs)

# === Historial de fotos ===
st.subheader("🗂 Historial de fotos guardadas")
history = get_history(limit=10)
data_photos = []
for h in history:
    fecha = h.get("fecha").strftime("%Y-%m-%d %H:%M:%S") if h.get("fecha") else "N/A"
    url = h.get("photo_url")
    hash_val = h.get("hash")
    data_photos.append({"Fecha": fecha, "URL": url, "Hash": hash_val})

df_photos = pd.DataFrame(data_photos)
st.dataframe(df_photos)

# === Botón de verificación de cambios ===
st.subheader("🔄 Verificación de foto")
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
            saved = save_photo(st.session_state.photo_url, current_hash)
            if saved:
                st.success("Foto nueva registrada en historial.")
            try:
                sid = send_whatsapp(f"📸 Nueva foto detectada: {st.session_state.photo_url}")
                st.success(f"Notificación enviada! SID: {sid}")
            except Exception as e:
                st.error(f"No se pudo enviar la notificación: {e}")
        else:
            st.info("No hay cambios en la foto o ya se notificó esta imagen.")

# === Mostrar última verificación ===
if st.session_state.last_checked > datetime.min:
    st.write(f"Última verificación: {st.session_state.last_checked.strftime('%Y-%m-%d %H:%M:%S')}")
