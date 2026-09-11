import requests

# --- API TIMES ---
times_cache = {}

def buscar_times(nome: str):

    nome = nome.strip().lower()

    if nome in times_cache:
        return times_cache[nome]

    url = (
        "https://www.thesportsdb.com/api/v1/json/3/searchteams.php"
        f"?t={nome}"
    )

    resposta = requests.get(url)
    dados = resposta.json()

    if dados["teams"] is None:
        times_cache[nome] = []  
        return []

    times = []

    for time in dados["teams"]:
        times.append({
            "nome": time["strTeam"],
            "pais": time["strCountry"],
            "liga": time["strLeague"],
            "escudo": time["strBadge"]
        })

    # Salva no cache
    times_cache[nome] = times

    return times
