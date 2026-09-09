from infrastructure.external import youtube_api_client

BUSCA_POR_ESPORTE = {
    "futebol": "futebol melhores momentos",
    "basquete": "NBA highlights",
    "ufc": "UFC highlights",
    "nhl": "NHL highlights",
    "formula1": "Formula 1 highlights",
}


def buscar_videos_por_esporte(esporte: str) -> list[dict]:
    busca = BUSCA_POR_ESPORTE.get(esporte, esporte)
    resultado = youtube_api_client.buscar(query=busca, max_results=12)
    itens = resultado["json"]["items"] if resultado["json"] else []

    videos = []
    for video in itens:
        videos.append({
            "titulo": video["snippet"]["title"],
            "canal": video["snippet"]["channelTitle"],
            "thumbnail": video["snippet"]["thumbnails"]["high"]["url"],
            "id": video["id"]["videoId"],
        })

    return videos


def buscar_videos_por_termo(q: str) -> list[dict]:
    q = q.strip()
    if not q:
        return []

    resultado = youtube_api_client.buscar(query=q, max_results=20, timeout=10)

    if resultado["status_code"] != 200:
        raise RuntimeError(resultado["text"])

    videos = []
    for video in resultado["json"].get("items", []):
        video_id = video.get("id", {}).get("videoId")
        if not video_id:
            continue

        snippet = video.get("snippet", {})
        videos.append({
            "titulo": snippet.get("title", "Sem título"),
            "canal": snippet.get("channelTitle", "Canal desconhecido"),
            "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url"),
            "id": video_id,
        })

    return videos
