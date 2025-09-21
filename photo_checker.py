# photo_checker.py
import requests
import hashlib
from notifier import notify_if_image_error
from db import get_latest_record, insert_photo_record
from datetime import datetime
import pytz

colombia = pytz.timezone("America/Bogota")

def download_image(url: str) -> bytes:
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        notify_if_image_error(f"Error descargando imagen: {e}")
        return None

def calculate_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

def check_and_update_photo():
    latest = get_latest_record()
    if not latest:
        return False, "No hay foto inicial en DB."
    try:
        img = download_image(latest["photo_url"])
        if not img:
            return False, "No se pudo descargar la imagen."
        new_hash = calculate_hash(img)
        if new_hash != latest.get("hash"):
            insert_photo_record(latest["photo_url"], new_hash)
            return True, "✅ Nueva foto detectada y guardada."
        return False, "ℹ️ No hubo cambios."
    except Exception as e:
        return False, f"Error verificando foto: {e}"
