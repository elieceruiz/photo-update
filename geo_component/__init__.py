import streamlit.components.v1 as components
import json

# Declaramos el componente (modo dev=False porque no tenemos server aparte)
_component_func = components.declare_component(
    "geo_component",
    path=str(__file__).replace("__init__.py", ""),  # busca el frontend.html
)

def get_geolocation(key="geo"):
    """Obtiene lat/lon desde el navegador usando un componente custom."""
    raw = _component_func(key=key, default="{}")
    try:
        return json.loads(raw)
    except Exception:
        return {"error": f"parse_fail: {raw}"}
