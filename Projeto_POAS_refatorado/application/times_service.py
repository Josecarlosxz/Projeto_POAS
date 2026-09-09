from infrastructure.external import sportsdb_client

_cache: dict[str, list[dict]] = {}


def buscar_time(nome: str) -> list[dict]:
    nome = nome.strip().lower()

    if nome in _cache:
        return _cache[nome]

    dados = sportsdb_client.buscar_times(nome)

    if dados.get("teams") is None:
        _cache[nome] = []
        return []

    times = [
        {
            "nome": time["strTeam"],
            "pais": time["strCountry"],
            "liga": time["strLeague"],
            "escudo": time["strBadge"],
        }
        for time in dados["teams"]
    ]

    _cache[nome] = times
    return times
