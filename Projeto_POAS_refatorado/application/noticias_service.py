from infrastructure.external import news_api_client

PALAVRAS_CHAVE = {
    "basquete": [
        "nba", "basketball", "lebron", "stephen curry",
        "warriors", "lakers", "celtics", "bucks", "knicks",
    ],
    "futebol_americano": [
        "nfl", "american football", "chiefs", "eagles", "cowboys",
        "packers", "49ers", "ravens", "patrick mahomes", "josh allen",
    ],
    "formula1": [
        "formula 1", "f1", "verstappen", "hamilton", "ferrari", "red bull",
        "mercedes", "mclaren", "leclerc", "norris", "russell", "aston martin",
    ],
}

QUERY_NEWS_API = {
    "basquete": '("NBA" OR "basketball")',
    "ufc": '("UFC" OR "MMA")',
    "futebol_americano": '("NFL" OR "American Football")',
    "formula1": '("Formula 1" OR "F1")',
}


def _texto_contem_alguma_palavra(texto: str, palavras: list[str]) -> bool:
    texto = texto.lower()
    return any(palavra in texto for palavra in palavras)


def _artigo_valido(artigo: dict) -> bool:
    return artigo.get("title") is not None and artigo.get("urlToImage") is not None


def obter_noticias_gerais() -> list[dict] | dict:
    """Notícias gerais de futebol (rota /api/noticias)."""
    resultado = news_api_client.buscar(query="soccer OR football")

    if resultado["status_code"] != 200:
        return {"erro": "Falha ao buscar notícias"}

    noticias = []
    for artigo in resultado["json"]["articles"][:20]:
        if not _artigo_valido(artigo):
            continue
        noticias.append({
            "titulo": artigo["title"],
            "descricao": artigo["description"],
            "imagem": artigo["urlToImage"],
            "link": artigo["url"],
            "fonte": artigo["source"]["name"],
            "data": artigo["publishedAt"],
        })

    return noticias


def obter_noticias_por_esporte(esporte: str) -> list[dict]:
    """Cobre basquete, ufc, futebol_americano e formula1."""
    resultado = news_api_client.buscar(query=QUERY_NEWS_API[esporte])
    artigos = resultado["json"]["articles"] if resultado["json"] else []

    noticias = []
    for artigo in artigos:
        if not _artigo_valido(artigo):
            continue

        if esporte == "ufc":
            titulo = artigo["title"].lower()
            if "ufc" in titulo or "mma" in titulo:
                noticias.append(artigo)
            continue

        texto = ((artigo["title"] or "") + " " + (artigo["description"] or ""))
        if not _texto_contem_alguma_palavra(texto, PALAVRAS_CHAVE[esporte]):
            continue

        if esporte == "basquete":
            noticias.append(artigo)
        else:
            noticias.append({
                "title": artigo["title"],
                "description": artigo["description"],
                "url": artigo["url"],
                "urlToImage": artigo["urlToImage"],
                "source": artigo["source"],
            })

    return noticias


def buscar_noticias_por_termo(q: str) -> list[dict]:
    """Barra de busca (rota /api/buscar-noticias)."""
    q = q.strip()
    if not q:
        return []

    termos = [termo.lower() for termo in q.split() if len(termo) >= 2]
    if not termos:
        return []

    consulta = " AND ".join(f'"{termo}"' for termo in termos)
    resultado = news_api_client.buscar(query=consulta, page_size=100, timeout=10)

    if resultado["status_code"] != 200:
        raise RuntimeError(resultado["text"])

    noticias = []
    for artigo in resultado["json"].get("articles", []):
        titulo = artigo.get("title") or ""
        descricao = artigo.get("description") or ""
        conteudo = artigo.get("content") or ""
        texto_completo = f"{titulo} {descricao} {conteudo}".lower()

        if not all(termo in texto_completo for termo in termos):
            continue
        if not titulo or not artigo.get("urlToImage"):
            continue

        noticias.append({
            "titulo": titulo,
            "descricao": descricao,
            "imagem": artigo["urlToImage"],
            "link": artigo.get("url"),
            "fonte": artigo.get("source", {}).get("name"),
            "data": artigo.get("publishedAt"),
        })

    return noticias[:20]
