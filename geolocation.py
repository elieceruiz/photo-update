# geolocation.py
from streamlit_js_eval import get_geolocation
import streamlit as st
from db import insert_access_log

def handle_geolocation(state):
    """
    Detecta la ubicación del usuario usando el navegador.
    - state: st.session_state de Streamlit
    Inicializa claves si no existen.
    Registra acceso en DB y actualiza state.geo_data.
    """
    # Inicializar claves
    if "access_logged" not in state:
        state.access_logged = False
    if "geo_data" not in state:
        state.geo_data = None

    # Solo ejecutar si no se ha registrado el acceso
    if not state.access_logged:
        geo = get_geolocation()
        if geo:
            if "coords" in geo:
                lat = geo["coords"]["latitude"]
                lon = geo["coords"]["longitude"]
                acc = geo["coords"].get("accuracy", "?")
                st.success(f"📍 Ubicación detectada: {lat:.6f}, {lon:.6f} (±{acc} m)")
                insert_access_log(lat=lat, lon=lon, acc=acc)
                state.geo_data = {"lat": lat, "lon": lon, "accuracy": acc}
                state.access_logged = True
            elif "error" in geo:
                st.warning(f"⚠️ Error navegador: {geo['error']}")
                insert_access_log(lat=None, lon=None, acc=None)
                state.access_logged = True
