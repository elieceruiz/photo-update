import streamlit as st
from datetime import datetime
import pytz
import hashlib
from urllib.parse import urlparse, parse_qs
from db import insert_photo_record

colombia = pytz.timezone("America/Bogota")

def show_url_input(latest, geo_data):
    """
    Muestra el input condicional de URL.
    Devuelve nuevo_url si fue ingresado, None si no.
    """
    url_mongo = latest.get("photo_url", "") if latest else ""
    nuevo_url = None

    # Caso: primer registro
    if not url_mongo:
        nuevo_url = st.text_input("✏️ Registrar primer URL de foto")

    # Caso: ya existe registro en Mongo y check detectó cambio
    elif st.session_state.get("show_input", False):
        nuevo_url = st.text_input("✏️ Ingresa nuevo enlace para comparar y registrar")

    return url_mongo, nuevo_url


def process_new_url(url_mongo, nuevo_url, geo_data):
    """
    Procesa un nuevo enlace ingresado:
    - Compara con el de Mongo
    - Muestra diferencias
    - Guarda en Mongo si es distinto
    - Maneja show_input
    """
    if not nuevo_url:
        return

    # Caso: link igual
    if url_mongo and url_mongo == nuevo_url:
        st.success("✅ El link en Mongo es IGUAL al nuevo. No se requiere actualización.")
        st.session_state.show_input = False
        return

    # Caso: link distinto → comparación
    if url_mongo:
        st.subheader("🧾 Comparación de URLs")
        st.error("❌ El link en Mongo es DIFERENTE al nuevo")

        mongo_params = parse_qs(urlparse(url_mongo).query) if url_mongo else {}
        nuevo_params = parse_qs(urlparse(nuevo_url).query)
        todas_claves = set(mongo_params.keys()) | set(nuevo_params.keys())

        diferencias = []
        for clave in todas_claves:
            val_mongo = mongo_params.get(clave, ["-"])[0]
            val_nuevo = nuevo_params.get(clave, ["-"])[0]
            if val_mongo != val_nuevo:
                diferencias.append((clave, val_mongo, val_nuevo))

        if diferencias:
            st.markdown("🔍 **Diferencias encontradas:**")
            for clave, val_mongo, val_nuevo in diferencias:
                st.markdown(f"- {clave} = {val_mongo}  (Mongo)")
                st.markdown(f"+ {clave} = {val_nuevo}  (Nuevo)")
        else:
            st.info("ℹ️ No se encontraron diferencias en los parámetros. Puede que cambie solo la parte base del link.")

    # Inspector DEBUG
    st.subheader("🛠️ Inspector DEBUG")
    hash_value = hashlib.sha256(nuevo_url.encode()).hexdigest()
    st.json({
        "Nuevo URL": nuevo_url,
        "Hash generado": hash_value,
        "Fecha (UTC)": datetime.utcnow().strftime("%d %b %y %H:%M"),
        "Geo Data": geo_data if geo_data else "❌ No detectada"
    })

    # Guardar en Mongo
    try:
        insert_photo_record(
            photo_url=nuevo_url,
            hash_value=hash_value,
            checked_at=datetime.utcnow().replace(tzinfo=pytz.UTC),
            geo_data=geo_data
        )
        print(f"✅ Guardado en Mongo: {nuevo_url}")
        st.success("✅ Nuevo enlace guardado en Mongo")
        st.session_state.show_input = False  # ocultar input tras guardar
    except Exception as e:
        st.error(f"💥 Error en insert_photo_record: {e}")
