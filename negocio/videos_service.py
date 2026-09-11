from urllib.parse import quote

import requests
from fastapi.responses import JSONResponse

from config import YOUTUBE_API_KEY


def videos(esporte: str):

    pesquisas = {
        "futebol": "futebol melhores momentos",
        "basquete": "NBA highlights",
        "ufc": "UFC highlights",
        "nhl": "NHL highlights",
        "formula1": "Formula 1 highlights"
    }

    busca = pesquisas.get(esporte, esporte)

    url = (
        "https://www.googleapis.com/youtube/v3/search"
        "?part=snippet"
        "&type=video"
        "&maxResults=12"
        f"&q={busca}"
        f"&key={YOUTUBE_API_KEY}"
    )

    resposta = requests.get(url)

    videos = []

    for video in resposta.json()["items"]:

        videos.append({
            "titulo": video["snippet"]["title"],
            "canal": video["snippet"]["channelTitle"],
            "thumbnail": video["snippet"]["thumbnails"]["high"]["url"],
            "id": video["id"]["videoId"]
        })

    return videos

def buscar_videos(q: str):

    q = q.strip()

    if not q:
        return []


    url = (
        "https://www.googleapis.com/youtube/v3/search"
        "?part=snippet"
        "&type=video"
        "&maxResults=20"
        f"&q={quote(q)}"
        f"&key={YOUTUBE_API_KEY}"
    )


    resposta = requests.get(
        url,
        timeout=10
    )


    if resposta.status_code != 200:

        return JSONResponse(
            status_code=500,
            content={
                "erro": "Falha ao buscar vídeos",
                "detalhes": resposta.text
            }
        )


    dados = resposta.json()

    videos = []


    for video in dados.get("items", []):

        video_id = video.get(
            "id",
            {}
        ).get("videoId")


        snippet = video.get(
            "snippet",
            {}
        )


        if not video_id:
            continue


        videos.append({

            "titulo":
                snippet.get(
                    "title",
                    "Sem título"
                ),

            "canal":
                snippet.get(
                    "channelTitle",
                    "Canal desconhecido"
                ),

            "thumbnail":
                snippet.get(
                    "thumbnails",
                    {}
                ).get(
                    "high",
                    {}
                ).get("url"),

            "id":
                video_id

        })


    return videos
