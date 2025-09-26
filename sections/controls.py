# sections/controls.py
import streamlit as st
from url_handler import show_url_input, process_new_url
from photo_checker import download_image

def render_controls(latest, geo_data, check_and_update_photo):
    # Input condicional
    url_mongo, nuevo_url = show_url_input(latest, geo_data)
    process_new_url(url_mongo, nuevo_url, geo_data)

    # Imagen actual
    if url_mongo:
        try:
            img_bytes = download_image(url_mongo)
            if img_bytes:
                st.image(img_bytes, caption="Miniatura actual")
            else:
                st.error("❌ No se pudo cargar la imagen")
        except Exception as e:
            st.error(f"❌ Error: {e}")
    else:
        st.warning("⚠️ No hay URL de foto en el último registro")

    # Botón de verificación
    if st.button("🔄 Verificar foto ahora"):
        changed, msg = check_and_update_photo()
        if changed:
            st.success(msg)
            st.session_state.show_input = True
        else:
            st.info(msg)
            st.session_state.show_input = False
