from urllib.parse import quote

import requests
from fastapi.responses import JSONResponse

from config import API_KEY


def obter_noticias():

    url = (
        "https://newsapi.org/v2/everything?"
        "q=soccer OR football"
        "&language=pt"
        "&sortBy=publishedAt"
        f"&apiKey={API_KEY}"
    )

    resposta = requests.get(url)

    if resposta.status_code != 200:
        return JSONResponse(
            status_code=500,
            content={"erro": "Falha ao buscar notícias"}
        )

    dados = resposta.json()

    noticias = []

    for artigo in dados["articles"][:20]:

        if artigo["title"] is None or artigo["urlToImage"] is None:
            continue

        noticias.append({
            "titulo": artigo["title"],
            "descricao": artigo["description"],
            "imagem": artigo["urlToImage"],
            "link": artigo["url"],
            "fonte": artigo["source"]["name"],
            "data": artigo["publishedAt"]
        })

    return noticias

def basquete():

    url = (
        "https://newsapi.org/v2/everything?"
        'q=("NBA" OR "basketball")'
        "&language=pt"
        "&sortBy=publishedAt"
        f"&apiKey={API_KEY}"
    )

    resposta = requests.get(url)

    artigos = resposta.json()["articles"]

    noticias = []

    palavras = [
        "nba",
        "basketball",
        "lebron",
        "stephen curry",
        "warriors",
        "lakers",
        "celtics",
        "bucks",
        "knicks"
    ]

    for artigo in artigos:

        if artigo["title"] is None or artigo["urlToImage"] is None:
            continue

        texto = (
            (artigo["title"] or "") +
            " " +
            (artigo["description"] or "")
        ).lower()

        if any(palavra in texto for palavra in palavras):
            noticias.append(artigo)

    return noticias

def ufc():

    url = (
        "https://newsapi.org/v2/everything?"
        'q=("UFC" OR "MMA")'
        "&language=pt"
        "&sortBy=publishedAt"
        f"&apiKey={API_KEY}"
    )

    resposta = requests.get(url)

    artigos = resposta.json()["articles"]

    noticias = []

    for artigo in artigos:

        if artigo["title"] is None or artigo["urlToImage"] is None:
            continue

        titulo = artigo["title"].lower()

        if (
            "ufc" in titulo
            or "mma" in titulo
        ):
            noticias.append(artigo)

    return noticias

def futebol_americano():

    url = (
        "https://newsapi.org/v2/everything?"
        'q=("NFL" OR "American Football")'
        "&language=pt"
        "&sortBy=publishedAt"
        f"&apiKey={API_KEY}"
    )

    resposta = requests.get(url)

    artigos = resposta.json()["articles"]

    noticias = []

    palavras = [
        "nfl",
        "american football",
        "chiefs",
        "eagles",
        "cowboys",
        "packers",
        "49ers",
        "ravens",
        "patrick mahomes",
        "josh allen"
    ]

    for artigo in artigos:
        
        if artigo["title"] is None or artigo["urlToImage"] is None:
            continue

        texto = (
            (artigo["title"] or "") +
            " " +
            (artigo["description"] or "")
        ).lower()

        if any(palavra in texto for palavra in palavras):

            noticias.append({
                "title": artigo["title"],
                "description": artigo["description"],
                "url": artigo["url"],
                "urlToImage": artigo["urlToImage"],
                "source": artigo["source"]
            })

    return noticias

def formula1():

    url = (
        "https://newsapi.org/v2/everything?"
        'q=("Formula 1" OR "F1")'
        '&language=pt'
        "&sortBy=publishedAt"
        f"&apiKey={API_KEY}"
    )

    resposta = requests.get(url)

    artigos = resposta.json()["articles"]

    noticias = []

    palavras = [
        "formula 1",
        "f1",
        "verstappen",
        "hamilton",
        "ferrari",
        "red bull",
        "mercedes",
        "mclaren",
        "leclerc",
        "norris",
        "russell",
        "aston martin"
    ]

    for artigo in artigos:

        texto = (
            (artigo["title"] or "") +
            " " +
            (artigo["description"] or "")
        ).lower()

        if any(palavra in texto for palavra in palavras):

            if not all([
                artigo.get("title"),
                artigo.get("description"),
                artigo.get("url"),
                artigo.get("urlToImage")
            ]):
                continue

            noticias.append({
                "title": artigo["title"],
                "description": artigo["description"],
                "url": artigo["url"],
                "urlToImage": artigo["urlToImage"],
                "source": artigo["source"]
            })

    return noticias

def buscar_noticias(q: str):
    q = q.strip()

    if not q:
        return []

    termos = [
        termo.lower()
        for termo in q.split()
        if len(termo) >= 2
    ]

    if not termos:
        return []

    consulta = " AND ".join(f'"{termo}"' for termo in termos)

    url = (
        "https://newsapi.org/v2/everything?"
        f"q={quote(consulta)}"
        "&language=pt"
        "&sortBy=publishedAt"
        "&pageSize=100"
        f"&apiKey={API_KEY}"
    )

    resposta = requests.get(url, timeout=10)

    if resposta.status_code != 200:
        return JSONResponse(
            status_code=500,
            content={
                "erro": "Falha ao buscar notícias",
                "detalhes": resposta.text
            }
        )

    dados = resposta.json()

    noticias = []

    for artigo in dados.get("articles", []):

        titulo = artigo.get("title") or ""
        descricao = artigo.get("description") or ""
        conteudo = artigo.get("content") or ""

        texto_completo = (
            f"{titulo} {descricao} {conteudo}"
        ).lower()

        if not all(termo in texto_completo for termo in termos):
            continue

        if not titulo:
            continue

        if not artigo.get("urlToImage"):
            continue

        noticias.append({
            "titulo": titulo,
            "descricao": descricao,
            "imagem": artigo["urlToImage"],
            "link": artigo.get("url"),
            "fonte": artigo.get("source", {}).get("name"),
            "data": artigo.get("publishedAt")
        })

    return noticias[:20]
