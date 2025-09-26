# photo_checker.py
# ============================================
# Descarga, verificación y actualización de fotos
# ============================================

import requests
import hashlib
from notifier import notify_if_image_error
from db import get_latest_record, insert_photo_record
from datetime import datetime
import pytz

# Zona horaria local (Bogotá)
colombia = pytz.timezone("America/Bogota")

# ==============================
# Descarga de imagen
# ==============================
def download_image(url: str) -> bytes:
    """
    Descarga la imagen desde una URL y devuelve su contenido en bytes.
    Si falla, notifica el error y retorna None.
    """
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        notify_if_image_error(f"Error descargando imagen: {e}")
        return None

# ==============================
# Hash de la imagen
# ==============================
def calculate_hash(content: bytes) -> str:
    """
    Calcula el hash SHA-256 de los bytes de una imagen.
    """
    return hashlib.sha256(content).hexdigest()

# ==============================
# Verificación y actualización
# ==============================
def check_and_update_photo():
    """
    Verifica si la foto más reciente ha cambiado (comparando hash).
    
    Flujo:
      1. Obtiene el último registro desde la DB.
      2. Descarga la foto actual.
      3. Calcula el hash y lo compara con el guardado.
      4. Si hay cambios → inserta un nuevo registro en la DB
         usando insert_photo_record() con:
            - photo_url
            - nuevo hash
            - fecha actual (Bogotá → convertida a UTC)
            - sin geo_data (None)
    Retorna:
      (status: bool, mensaje: str)
    """
    latest = get_latest_record()
    if not latest:
        return False, "No hay foto inicial en DB."

    try:
        img = download_image(latest["photo_url"])
        if not img:
            return False, "No se pudo descargar la imagen."

        # Calcular nuevo hash
        new_hash = calculate_hash(img)

        # Comparar con el último guardado
        if new_hash != latest.get("hash"):
            # Convertir fecha local a UTC
            now_bogota = datetime.now(colombia)
            now_utc = now_bogota.astimezone(pytz.UTC)

            # Insertar nuevo registro en Mongo
            insert_photo_record(
                latest["photo_url"],   # URL foto
                new_hash,              # hash nuevo
                checked_at=now_utc,    # fecha de verificación
                geo_data=None          # opcional (no aplica aquí)
            )

            return True, "✅ Nueva foto detectada y guardada."

        return False, "ℹ️ No hubo cambios."
    except Exception as e:
        return False, f"Error verificando foto: {e}"