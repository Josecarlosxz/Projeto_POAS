from typing import Optional

import requests

from infrastructure.config import NEWS_API_KEY

BASE_URL = "https://newsapi.org/v2/everything"


def buscar(
    query: str,
    language: str = "pt",
    sort_by: str = "publishedAt",
    page_size: Optional[int] = None,
    timeout: Optional[int] = None,
) -> dict:
    """Faz a chamada crua à NewsAPI e devolve status, texto e json (se houver)."""

    params = {
        "q": query,
        "language": language,
        "sortBy": sort_by,
        "apiKey": NEWS_API_KEY,
    }
    if page_size:
        params["pageSize"] = page_size

    kwargs = {"params": params}
    if timeout:
        kwargs["timeout"] = timeout

    resposta = requests.get(BASE_URL, **kwargs)

    return {
        "status_code": resposta.status_code,
        "text": resposta.text,
        "json": resposta.json() if resposta.status_code == 200 else None,
    }
