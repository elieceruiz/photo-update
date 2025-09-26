import streamlit as st
from datetime import datetime
import pytz
from db import insert_photo_record
from sections.inspector import show_debug, compare_urls

# ---------------------------
# Función para manejar input de URL
# ---------------------------

def handle_url_input(latest, geo_data):
    """
    Maneja la entrada de URL para:
    - Registrar primer URL
    - Actualizar URL existente
    Retorna True si se guardó un nuevo registro.
    """
    # URL actual en Mongo
    url_mongo = latest.get("photo_url", "") if latest else ""
    nuevo_url = None

    # Mostrar input según sea primer registro o actualización
    if not url_mongo:
        nuevo_url = st.text_input("✏️ Registrar primer URL de foto")
    elif st.session_state.show_input:
        nuevo_url = st.text_input("✏️ Ingresa nuevo enlace para comparar y registrar")

    if nuevo_url:
        # Caso: link igual → no se actualiza
        if url_mongo and url_mongo == nuevo_url:
            st.success("✅ El link en Mongo es IGUAL al nuevo. No se requiere actualización.")
            st.session_state.show_input = False
            return False

        # Caso: link distinto → mostrar diferencias
        if url_mongo:
            compare_urls(url_mongo, nuevo_url)

        # Mostrar debug y generar hash
        hash_value = show_debug(nuevo_url, geo_data)

        # Guardar registro en Mongo
        try:
            insert_photo_record(
                photo_url=nuevo_url,
                hash_value=hash_value,
                checked_at=datetime.utcnow().replace(tzinfo=pytz.UTC),
                geo_data=geo_data
            )
            if url_mongo:
                st.success("✅ Nuevo enlace guardado en Mongo")
            else:
                st.success("✅ Primer enlace guardado en Mongo")
            st.session_state.show_input = False
            return True
        except Exception as e:
            st.error(f"💥 Error en insert_photo_record: {e}")
            return False

    return False
