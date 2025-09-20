import requests
from bs4 import BeautifulSoup

def get_current_profile_pic_url(instagram_url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(instagram_url, headers=headers)
    if r.status_code != 200:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    og_image = soup.find("meta", property="og:image")
    if og_image:
        return og_image.get("content")
    return None
