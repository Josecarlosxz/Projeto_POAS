import requests

BASE_URL = "https://www.thesportsdb.com/api/v1/json/3/searchteams.php"


def buscar_times(nome: str) -> dict:
    """Faz a chamada crua à TheSportsDB e devolve o json bruto."""
    resposta = requests.get(BASE_URL, params={"t": nome})
    return resposta.json()
