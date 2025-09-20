# checker.py
import requests
import hashlib
from bs4 import BeautifulSoup

def get_current_profile_pic_url(instagram_url: str) -> str:
    """
    Obtiene la URL de la foto de perfil actual de Instagram desde la URL base del perfil.
    Retorna None si no se puede obtener o en caso de error.
    NOTA: Para cuentas privadas es probable que no devuelva la URL real sin login.
    """
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/138.0.7204.243 Safari/537.36")
    }
    try:
        r = requests.get(instagram_url, headers=headers, timeout=10)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        og_image = soup.find("meta", property="og:image")
        if og_image:
            return og_image.get("content")
    except Exception as e:
        print(f"Error al obtener URL de perfil: {e}")
    return None

def get_image_bytes(url: str) -> bytes:
    """
    Descarga la imagen desde la URL indicada y devuelve los bytes.
    Retorna None si falla la descarga o status != 200.
    """
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/138.0.7204.243 Safari/537.36"),
        "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
        "Referer": "https://www.instagram.com/"
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            return r.content
    except Exception as e:
        print(f"Error al descargar imagen: {e}")
    return None

def hash_image(image_bytes: bytes) -> str:
    """
    Calcula y devuelve hash SHA-256 para detectar cambios en la imagen.
    """
    return hashlib.sha256(image_bytes).hexdigest()

def has_photo_changed(current_url: str, last_hash: str = None):
    """
    Descarga imagen actual y compara hash con el previo para detectar cambios.
    Devuelve (bool, str) indicando cambio y hash actual o previo.
    """
    image_bytes = get_image_bytes(current_url)
    if not image_bytes:
        return False, last_hash
    current_hash = hash_image(image_bytes)
    if last_hash != current_hash:
        return True, current_hash
    return False, last_hash
