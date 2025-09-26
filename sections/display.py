# sections/display.py
import streamlit as st
from photo_checker import check_and_update_photo, download_image

# ---------------------------
# Funciones para mostrar imagen y verificación manual
# ---------------------------

def show_image(url_mongo, nuevo_guardado):
    """
    Muestra la imagen actual si existe y alerta si no hay foto registrada.
    """
    try:
        if url_mongo:
            img_bytes = download_image(url_mongo)
            if img_bytes:
                st.image(img_bytes, caption="Miniatura actual")
            else:
                st.error("❌ No se pudo cargar la imagen")
        elif not url_mongo and not nuevo_guardado:
            st.warning("⚠️ No hay fotos registradas en la base de datos.")
    except Exception as e:
        st.error(f"❌ Error: {e}")


def manual_verification():
    """
    Botón para verificación manual de la foto.
    Actualiza session_state.show_input según si hubo cambio.
    """
    if st.button("🔄 Verificar foto ahora"):
        changed, msg = check_and_update_photo()
        st.session_state.show_input = changed
        if changed:
            st.success(msg)
        else:
            st.info(msg)
