import os
import json
import streamlit.components.v1 as components

# ========================================================
# Declaración del componente personalizado de geolocalización
# ========================================================

# ⚠️ Importante:
# Aquí no apuntamos al archivo `frontend.html` directamente,
# sino al directorio donde vive. Streamlit buscará
# automáticamente el `frontend.html` dentro de esa carpeta.
_component_func = components.declare_component(
    "geo_component",
    path=os.path.dirname(__file__),  # Carpeta geo_component/
)


def get_geolocation(key: str = "geo") -> dict:
    """
    Obtiene la ubicación del usuario desde el navegador usando
    navigator.geolocation (HTML5).

    🔹 Parámetros:
        key (str): Identificador único del componente en Streamlit.

    🔹 Retorna un diccionario:
        - Si éxito:
            {
              "lat": 6.3381,
              "lon": -75.5564,
              "accuracy": 20
            }
        - Si error:
            {
              "error": "mensaje de error"
            }
    """
    raw = _component_func(key=key, default="{}")
    try:
        return json.loads(raw)
    except Exception:
        return {"error": f"parse_fail: {raw}"}
