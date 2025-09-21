import os
import json
import streamlit.components.v1 as components

# Declaramos el componente custom apuntando al archivo frontend.html
_component_func = components.declare_component(
    "geo_component",
    path=os.path.join(os.path.dirname(__file__), "frontend.html"),
)

def get_geolocation(key="geo"):
    """
    Obtiene lat/lon desde el navegador usando navigator.geolocation.

    🔹 Retorna un dict:
        { "lat": 6.3381, "lon": -75.5564, "accuracy": 20 }
    🔹 En caso de error:
        { "error": "mensaje de error" }
    """
    raw = _component_func(key=key, default="{}")
    try:
        return json.loads(raw)
    except Exception:
        return {"error": f"parse_fail: {raw}"}
