# main.py
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import json  # 👈 necesario para parsear la respuesta JS

from checker import get_image_bytes, has_photo_changed
from db import save_photo, get_last_hash, get_last_photo_url
from notifier import send_whatsapp
from logs import log_access, get_access_logs

from streamlit_javascript import st_javascript

st.set_page_config(page_title="Photo Update", layout="centered")
st.title("📸 Photo Update")

# =========================
# Estados iniciales
# =========================
if "last_hash" not in st.session_state:
    st.session_state.last_hash = get_last_hash()
if "photo_url" not in st.session_state:
    st.session_state.photo_url = get_last_photo_url() or st.secrets.get("INITIAL_PHOTO_URL", "")
if "notified_hash" not in st.session_state:
    st.session_state.notified_hash = None
if "last_checked" not in st.session_state:
    st.session_state.last_checked = datetime.min
if "access_logged" not in st.session_state:
    st.session_state.access_logged = False

# =========================
# Detección de ubicación con JS (navigator.geolocation)
# =========================
if not st.session_state.access_logged:
    st.info("Intentando obtener ubicación desde tu navegador (se pedirá permiso)...")

    js_code = """
    (async () => {
      return new Promise((resolve) => {
        if (!navigator.geolocation) {
          resolve("{\\"error\\": \\"no_support\\"}");
          return;
        }
        navigator.geolocation.getCurrentPosition(
          (pos) => {
            resolve(JSON.stringify({
              lat: pos.coords.latitude,
              lon: pos.coords.longitude,
              accuracy: pos.coords.accuracy
            }));
          },
          (err) => {
            resolve(JSON.stringify({ error: err.message || err.code }));
          },
          { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
        );
      });
    })();
    """

    raw = st_javascript(js_code, key="geo_js")

    # 🔎 Debug: mostrar lo que llegó crudo
    st.write("🔎 Respuesta cruda del navegador:", raw)

    if raw is None:
        st.info("⌛ Esperando respuesta del navegador...")
    else:
        try:
            res = json.loads(raw)
        except Exception:
            st.error(f"⚠️ No se pudo parsear la respuesta: {raw}")
            res = {}

        if isinstance(res, dict) and res.get("error"):
            st.warning(f"⚠️ No se obtuvo ubicación desde el navegador: {res.get('error')}")
            log_access(lat=None, lon=None)
            st.session_state.access_logged = True
        elif isinstance(res, dict) and "lat" in res and "lon" in res:
            lat = float(res["lat"])
            lon = float(res["lon"])
            acc = res.get("accuracy")
            st.success(f"📍 Ubicación detectada: lat {lat:.6f}, lon {lon:.6f} (±{acc} m)")
            log_access(lat=lat, lon=lon)
            st.session_state.access_logged = True
        else:
            st.error(f"❌ Respuesta inesperada tras parseo: {res}")

# =========================
# Inspector de estado
# =========================
st.subheader("🔍 Inspector de estado")

st.write(f"**Último Hash:** {st.session_state.last_hash or 'N/A'}")
st.write(
    f"**Última verificación:** "
    f"{st.session_state.last_checked if st.session_state.last_checked > datetime.min else 'Nunca'}"
)

image_bytes = get_image_bytes(st.session_state.photo_url) if st.session_state.photo_url else None
if image_bytes:
    st.image(image_bytes, caption="Miniatura actual")
else:
    st.warning("No se pudo cargar la miniatura desde la URL guardada.")
    nueva_url = st.text_input("Ingrese nueva URL de miniatura Instagram")
    if nueva_url and nueva_url != st.session_state.photo_url:
        st.session_state.photo_url = nueva_url
        st.info("✅ URL actualizada. Presiona 'Verificar actualización'.")

# =========================
# Historial de accesos
# =========================
st.subheader("📜 Historial de accesos recientes")
logs = get_access_logs(limit=10)
data = []
for log in logs:
    fecha = log.get("fecha").strftime("%Y-%m-%d %H:%M:%S")
    lat = log.get("latitud")
    lon = log.get("longitud")
    data.append({"Fecha": fecha, "Latitud": lat, "Longitud": lon})

df_logs = pd.DataFrame(data)
st.dataframe(df_logs)

# =========================
# Botón verificación
# =========================
min_interval = timedelta(minutes=10)
if st.button("Verificar actualización"):
    now = datetime.now()
    if now - st.session_state.last_checked < min_interval:
        st.warning(f"⏳ Espera {int(min_interval.total_seconds()/60)} minutos entre chequeos.")
    else:
        st.session_state.last_checked = now
        changed, current_hash = has_photo_changed(
            st.session_state.photo_url, st.session_state.last_hash
        )
        if changed and st.session_state.notified_hash != current_hash:
            st.session_state.last_hash = current_hash
            st.session_state.notified_hash = current_hash
            save_photo(st.session_state.photo_url, current_hash)
            try:
                sid = send_whatsapp(
                    f"📸 Nueva foto detectada: {st.session_state.photo_url}"
                )
                st.success(f"✅ Notificación enviada! SID: {sid}")
            except Exception as e:
                st.error(f"❌ No se pudo enviar la notificación: {e}")
        else:
            st.info("ℹ️ No hay cambios en la foto o ya se notificó esta imagen.")
