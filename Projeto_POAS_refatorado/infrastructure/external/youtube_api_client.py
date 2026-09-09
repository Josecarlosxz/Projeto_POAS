from typing import Optional

import requests

from infrastructure.config import YOUTUBE_API_KEY

BASE_URL = "https://www.googleapis.com/youtube/v3/search"


def buscar(query: str, max_results: int = 12, timeout: Optional[int] = None) -> dict:
    """Faz a chamada crua à YouTube Data API e devolve status, texto e json (se houver)."""

    params = {
        "part": "snippet",
        "type": "video",
        "maxResults": max_results,
        "q": query,
        "key": YOUTUBE_API_KEY,
    }

    kwargs = {"params": params}
    if timeout:
        kwargs["timeout"] = timeout

    resposta = requests.get(BASE_URL, **kwargs)

    return {
        "status_code": resposta.status_code,
        "text": resposta.text,
        "json": resposta.json() if resposta.status_code == 200 else None,
    }
