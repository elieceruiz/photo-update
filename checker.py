# checker.py
import requests
import hashlib
from bs4 import BeautifulSoup

def get_image_bytes(url: str) -> bytes:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/138.0.7204.243 Safari/537.36",
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
    return hashlib.sha256(image_bytes).hexdigest()

def has_photo_changed(current_url: str, last_hash: str = None):
    image_bytes = get_image_bytes(current_url)
    if not image_bytes:
        return False, last_hash
    current_hash = hash_image(image_bytes)
    if last_hash != current_hash:
        return True, current_hash
    return False, last_hash
