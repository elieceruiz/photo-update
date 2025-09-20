# checker.py
import requests
from bs4 import BeautifulSoup
import hashlib

def get_current_profile_pic_url(instagram_url: str) -> str:
    """
    Devuelve la URL de la foto de perfil actual desde Instagram.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/138.0.7204.243 Safari/537.36"
    }
    r = requests.get(instagram_url, headers=headers)
    if r.status_code != 200:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    og_image = soup.find("meta", property="og:image")
    if og_image:
        return og_image.get("content")
    return None

def get_image_bytes(url: str) -> bytes:
    """
    Descarga la imagen desde la URL y devuelve los bytes.
    """
    r = requests.get(url)
    if r.status_code == 200:
        return r.content
    return None

def hash_image(image_bytes: bytes) -> str:
    """
    Calcula el hash SHA-256 de los bytes de la imagen.
    """
    return hashlib.sha256(image_bytes).hexdigest()

def has_photo_changed(current_url: str, last_hash: str = None):
    """
    Devuelve (bool, str):
      - True si la foto cambió
      - El hash actual de la imagen
    """
    image_bytes = get_image_bytes(current_url)
    if not image_bytes:
        return False, last_hash

    current_hash = hash_image(image_bytes)

    if last_hash != current_hash:
        return True, current_hash
    return False, last_hash
