"""
Regras da NFL, em funções puras (sem banco): estrutura, calendário de 17 jogos, classificação
por divisão, cabeças de chave (seeds) e chaveamento dos playoffs.

Estrutura fixa, como na NFL: 2 conferências x 4 divisões x 4 times = 32 times.
"""
import random
from fractions import Fraction
from typing import Dict, List, Optional

from fastapi import HTTPException

NUM_CONFERENCIAS = 2
DIVISOES_POR_CONFERENCIA = 4
TIMES_POR_DIVISAO = 4
SEMANAS_TEMPORADA = 18  # 17 jogos + 1 semana de folga por time
VAGAS_PLAYOFF_POR_CONFERENCIA = 7  # 4 campeões de divisão + 3 wild cards

ETAPA_WILD_CARD = "Wild Card"
ETAPA_DIVISIONAL = "Divisional"
ETAPA_FINAL_CONFERENCIA = "Final de Conferência"
ETAPA_SUPER_BOWL = "Super Bowl"


# ----------------------------------------------------------------------
# Estrutura (validação)
# ----------------------------------------------------------------------

def normalizar_conferencias(conferencias) -> Dict[str, Dict[str, List[str]]]:
    """Valida e normaliza {conferência: {divisão: [4 times]}}: 2 conferências, 4 divisões, 4 times."""
    if not isinstance(conferencias, dict) or len(conferencias) != NUM_CONFERENCIAS:
        raise HTTPException(status_code=400, detail=f"A NFL precisa de exatamente {NUM_CONFERENCIAS} conferências")

    normalizado: Dict[str, Dict[str, List[str]]] = {}
    nomes_conferencias = set()
    times_vistos = set()

    for nome_conferencia, divisoes in conferencias.items():
        nome_conf = (nome_conferencia or "").strip() if isinstance(nome_conferencia, str) else ""
        if not nome_conf:
            raise HTTPException(status_code=400, detail="O nome da conferência não pode ficar em branco")
        if nome_conf.lower() in nomes_conferencias:
            raise HTTPException(status_code=400, detail="As conferências precisam ter nomes diferentes")
        nomes_conferencias.add(nome_conf.lower())

        if not isinstance(divisoes, dict) or len(divisoes) != DIVISOES_POR_CONFERENCIA:
            raise HTTPException(
                status_code=400,
                detail=f"A conferência {nome_conf} precisa de exatamente {DIVISOES_POR_CONFERENCIA} divisões"
            )

        divisoes_norm: Dict[str, List[str]] = {}
        nomes_divisoes = set()
        for nome_divisao, times in divisoes.items():
            nome_div = (nome_divisao or "").strip() if isinstance(nome_divisao, str) else ""
            if not nome_div:
                raise HTTPException(status_code=400, detail=f"Há uma divisão sem nome na conferência {nome_conf}")
            if nome_div.lower() in nomes_divisoes:
                raise HTTPException(status_code=400, detail=f"A conferência {nome_conf} tem divisões com o mesmo nome")
            nomes_divisoes.add(nome_div.lower())

            if not isinstance(times, list):
                raise HTTPException(status_code=400, detail=f"Times inválidos na divisão {nome_div}")
            times_norm = [t.strip() for t in times if isinstance(t, str) and t.strip()]
            if len(times_norm) != TIMES_POR_DIVISAO:
                raise HTTPException(
                    status_code=400,
                    detail=f"A divisão {nome_div} ({nome_conf}) precisa de exatamente {TIMES_POR_DIVISAO} times"
                )
            for time in times_norm:
                if time.lower() in times_vistos:
                    raise HTTPException(status_code=400, detail=f"O time '{time}' aparece mais de uma vez")
                times_vistos.add(time.lower())

            divisoes_norm[nome_div] = times_norm

        normalizado[nome_conf] = divisoes_norm

    return normalizado


def listar_times(conferencias: Dict[str, Dict[str, List[str]]]) -> List[str]:
    return [t for divisoes in conferencias.values() for times in divisoes.values() for t in times]


# ----------------------------------------------------------------------
# Calendário: 17 jogos por time, pela fórmula da NFL
# ----------------------------------------------------------------------

def _montar_jogos(conferencias: Dict[str, Dict[str, List[str]]]) -> List[tuple]:
    """
    Devolve os 272 jogos como (mandante, visitante). Cada time joga 17:
      6  contra os 3 rivais da própria divisão (ida e volta)
      4  contra todos os times de uma divisão da própria conferência (divisões pareadas: 1ª-2ª e 3ª-4ª)
      4  contra todos os times da divisão de mesma posição na outra conferência
      2  contra os times de mesma posição nas outras duas divisões da própria conferência
      1  contra um time de outra divisão da outra conferência
    """
    estrutura = [list(divs.values()) for divs in conferencias.values()]  # [conf][divisão] -> [times]
    n_div, n_time = DIVISOES_POR_CONFERENCIA, TIMES_POR_DIVISAO
    jogos: List[tuple] = []

    # 1) dentro da divisão, ida e volta
    for c in range(NUM_CONFERENCIAS):
        for d in range(n_div):
            times = estrutura[c][d]
            for i in range(n_time):
                for j in range(i + 1, n_time):
                    jogos.append((times[i], times[j]))
                    jogos.append((times[j], times[i]))

    # 2) divisão pareada da mesma conferência (todos contra todos, uma vez)
    for c in range(NUM_CONFERENCIAS):
        for d_a, d_b in ((0, 1), (2, 3)):
            for i in range(n_time):
                for j in range(n_time):
                    a, b = estrutura[c][d_a][i], estrutura[c][d_b][j]
                    jogos.append((a, b) if (i + j) % 2 == 0 else (b, a))

    # 3) outra conferência, divisão de mesma posição (todos contra todos, uma vez)
    for d in range(n_div):
        for i in range(n_time):
            for j in range(n_time):
                a, b = estrutura[0][d][i], estrutura[1][d][j]
                jogos.append((a, b) if (i + j + d) % 2 == 0 else (b, a))

    # 4) mesma posição nas duas divisões restantes da própria conferência
    for c in range(NUM_CONFERENCIAS):
        for d_a, d_b in ((0, 2), (0, 3), (1, 2), (1, 3)):
            for k in range(n_time):
                a, b = estrutura[c][d_a][k], estrutura[c][d_b][k]
                jogos.append((a, b) if (k + c + d_a + d_b) % 2 == 0 else (b, a))

    # 5) 17º jogo: time da posição k da divisão d x time da posição k da divisão d+1 da outra conferência
    for d in range(n_div):
        for k in range(n_time):
            a, b = estrutura[0][d][k], estrutura[1][(d + 1) % n_div][k]
            jogos.append((a, b) if (d + k) % 2 == 0 else (b, a))

    return jogos


def _atribuir_semanas(jogos: List[tuple], semanas: int, max_iteracoes: int, rng: random.Random) -> Optional[List[int]]:
    """
    Distribui os jogos em semanas sem nenhum time jogar duas vezes na mesma semana
    (coloração de arestas por busca local: quando não cabe, desaloja o jogo em conflito).
    Devolve None se não achar solução dentro do limite de iterações.
    """
    n = len(jogos)
    atribuicao: List[Optional[int]] = [None] * n
    ocupacao: List[Dict[str, int]] = [dict() for _ in range(semanas)]

    fila = list(range(n))
    rng.shuffle(fila)

    def colocar(idx: int, semana: int) -> None:
        a, b = jogos[idx]
        atribuicao[idx] = semana
        ocupacao[semana][a] = idx
        ocupacao[semana][b] = idx

    def retirar(idx: int) -> None:
        a, b = jogos[idx]
        semana = atribuicao[idx]
        atribuicao[idx] = None
        del ocupacao[semana][a]
        del ocupacao[semana][b]

    iteracoes = 0
    while fila and iteracoes < max_iteracoes:
        iteracoes += 1
        idx = fila.pop()
        a, b = jogos[idx]

        conflitos_por_semana = []
        for w in range(semanas):
            conflitantes = {ocupacao[w].get(a), ocupacao[w].get(b)} - {None}
            conflitos_por_semana.append(len(conflitantes))

        menor = min(conflitos_por_semana)
        candidatas = [w for w in range(semanas) if conflitos_por_semana[w] == menor]
        semana = rng.choice(candidatas)

        for time in (a, b):
            conflitante = ocupacao[semana].get(time)
            if conflitante is not None:
                retirar(conflitante)
                fila.append(conflitante)

        colocar(idx, semana)

    return atribuicao if not fila else None  # type: ignore[return-value]


def _atribuir_semanas_guloso(jogos: List[tuple]) -> List[int]:
    """Último recurso: abre semanas novas quando preciso. Sempre termina."""
    ocupacao: List[set] = []
    atribuicao = []
    for a, b in jogos:
        for w, ocupados in enumerate(ocupacao):
            if a not in ocupados and b not in ocupados:
                ocupados.update((a, b))
                atribuicao.append(w)
                break
        else:
            ocupacao.append({a, b})
            atribuicao.append(len(ocupacao) - 1)
    return atribuicao


def gerar_calendario(conferencias: Dict[str, Dict[str, List[str]]], rng: Optional[random.Random] = None) -> List[tuple]:
    """Sorteia a temporada: devolve [(mandante, visitante, semana)] com semanas de 1 em diante."""
    rng = rng or random.Random()
    jogos = _montar_jogos(conferencias)

    atribuicao = None
    for semanas in range(SEMANAS_TEMPORADA, SEMANAS_TEMPORADA + 4):
        atribuicao = _atribuir_semanas(jogos, semanas, 80000, rng)
        if atribuicao is not None:
            break
    if atribuicao is None:
        atribuicao = _atribuir_semanas_guloso(jogos)

    # compacta (se alguma semana ficou vazia) e embaralha a ordem de apresentação dentro da semana
    usadas = sorted(set(atribuicao))
    renumeracao = {w: i + 1 for i, w in enumerate(usadas)}
    calendario = [(casa, visitante, renumeracao[w]) for (casa, visitante), w in zip(jogos, atribuicao)]
    rng.shuffle(calendario)
    calendario.sort(key=lambda j: j[2])
    return calendario


# ----------------------------------------------------------------------
# Classificação e cabeças de chave (seeds)
# ----------------------------------------------------------------------

def _porcentagem(vitorias: int, derrotas: int, empates: int) -> Fraction:
    """Aproveitamento da NFL: empate vale meia vitória."""
    jogos = vitorias + derrotas + empates
    return Fraction(2 * vitorias + empates, 2 * jogos) if jogos else Fraction(0)


def _estatisticas(conferencias: Dict[str, Dict[str, List[str]]], jogos: list) -> Dict[str, dict]:
    mapa = {
        time: (conf, divisao)
        for conf, divisoes in conferencias.items()
        for divisao, times in divisoes.items()
        for time in times
    }
    zerar = lambda: {"v": 0, "d": 0, "e": 0, "pf": 0, "pa": 0, "dv": 0, "dd": 0, "de": 0,
                     "cv": 0, "cd": 0, "ce": 0, "seq": []}
    stats = {time: zerar() for time in mapa}

    for jogo in sorted(jogos, key=lambda j: (j.rodada, j.id or 0)):
        casa, visitante = stats.get(jogo.time_casa), stats.get(jogo.time_visitante)
        if casa is None or visitante is None:
            continue

        mesma_conferencia = mapa[jogo.time_casa][0] == mapa[jogo.time_visitante][0]
        mesma_divisao = mesma_conferencia and mapa[jogo.time_casa][1] == mapa[jogo.time_visitante][1]

        casa["pf"] += jogo.gols_casa
        casa["pa"] += jogo.gols_visitante
        visitante["pf"] += jogo.gols_visitante
        visitante["pa"] += jogo.gols_casa

        if jogo.gols_casa > jogo.gols_visitante:
            resultados = (("v", casa, "V"), ("d", visitante, "D"))
        elif jogo.gols_casa < jogo.gols_visitante:
            resultados = (("d", casa, "D"), ("v", visitante, "V"))
        else:
            resultados = (("e", casa, "E"), ("e", visitante, "E"))

        for campo, time_stats, letra in resultados:
            time_stats[campo] += 1
            time_stats["seq"].append(letra)
            if mesma_conferencia:
                time_stats["c" + campo] += 1
            if mesma_divisao:
                time_stats["d" + campo] += 1

    return stats


def _confronto_direto(a: str, b: str, jogos: list) -> int:
    """+1 se 'a' venceu mais vezes que 'b' nos jogos entre os dois, -1 se o contrário, 0 se igual."""
    vitorias_a = vitorias_b = 0
    for jogo in jogos:
        if {jogo.time_casa, jogo.time_visitante} != {a, b} or jogo.gols_casa == jogo.gols_visitante:
            continue
        vencedor = jogo.time_casa if jogo.gols_casa > jogo.gols_visitante else jogo.time_visitante
        if vencedor == a:
            vitorias_a += 1
        else:
            vitorias_b += 1
    return (vitorias_a > vitorias_b) - (vitorias_a < vitorias_b)


def _ordenar(times: List[str], stats: Dict[str, dict], jogos: list, usar_divisao: bool) -> List[str]:
    """
    Desempate simplificado, na ordem da NFL: aproveitamento geral; confronto direto (quando são
    exatamente 2 times empatados); aproveitamento na divisão (só entre times da mesma divisão);
    aproveitamento na conferência; saldo de pontos; pontos marcados.
    Não implementa força de tabela/vitórias comuns, nem confronto direto entre 3 ou mais times.
    """
    def pct_geral(t):
        s = stats[t]
        return _porcentagem(s["v"], s["d"], s["e"])

    def chave(t):
        s = stats[t]
        pct_divisao = _porcentagem(s["dv"], s["dd"], s["de"]) if usar_divisao else Fraction(0)
        return (-pct_geral(t), -pct_divisao, -_porcentagem(s["cv"], s["cd"], s["ce"]), -(s["pf"] - s["pa"]), -s["pf"])

    ordenados = sorted(times, key=chave)

    resultado: List[str] = []
    i = 0
    while i < len(ordenados):
        j = i
        while j < len(ordenados) and pct_geral(ordenados[j]) == pct_geral(ordenados[i]):
            j += 1
        grupo = ordenados[i:j]
        if len(grupo) == 2 and _confronto_direto(grupo[0], grupo[1], jogos) < 0:
            grupo = [grupo[1], grupo[0]]
        resultado += grupo
        i = j
    return resultado


def _linha_tabela(time: str, stats: Dict[str, dict]) -> dict:
    s = stats[time]
    return {
        "time": time,
        "jogos": s["v"] + s["d"] + s["e"],
        "vitorias": s["v"], "derrotas": s["d"], "empates": s["e"],
        "aproveitamento": round(float(_porcentagem(s["v"], s["d"], s["e"])), 3),
        "pontos_marcados": s["pf"], "pontos_sofridos": s["pa"], "saldo_pontos": s["pf"] - s["pa"],
        "record_divisao": f'{s["dv"]}-{s["dd"]}-{s["de"]}',
        "record_conferencia": f'{s["cv"]}-{s["cd"]}-{s["ce"]}',
        "ultimos_5": s["seq"][-5:],
    }


def calcular_seeds(conferencias: Dict[str, Dict[str, List[str]]], jogos: list, stats: Optional[dict] = None) -> Dict[str, List[dict]]:
    """
    Seeds 1-4 = campeões de divisão (ordenados por campanha); seeds 5-7 = os 3 melhores
    entre os demais times da conferência (wild cards).
    """
    stats = stats or _estatisticas(conferencias, jogos)
    seeds: Dict[str, List[dict]] = {}

    for conf, divisoes in conferencias.items():
        campeoes = {}
        for divisao, times in divisoes.items():
            campeoes[_ordenar(times, stats, jogos, usar_divisao=True)[0]] = divisao

        ordem_campeoes = _ordenar(list(campeoes), stats, jogos, usar_divisao=False)
        restantes = [t for times in divisoes.values() for t in times if t not in campeoes]
        wild_cards = _ordenar(restantes, stats, jogos, usar_divisao=False)[:VAGAS_PLAYOFF_POR_CONFERENCIA - len(ordem_campeoes)]

        lista = [{"time": t, "tipo": "Campeão de divisão", "divisao": campeoes[t]} for t in ordem_campeoes]
        lista += [{"time": t, "tipo": "Wild Card", "divisao": None} for t in wild_cards]
        for posicao, item in enumerate(lista, start=1):
            item["seed"] = posicao
        seeds[conf] = lista

    return seeds


def calcular_classificacao(conferencias: Dict[str, Dict[str, List[str]]], jogos_finalizados: list) -> dict:
    stats = _estatisticas(conferencias, jogos_finalizados)
    seeds = calcular_seeds(conferencias, jogos_finalizados, stats)

    resultado = {}
    for conf, divisoes in conferencias.items():
        resultado[conf] = {
            "divisoes": {
                divisao: [_linha_tabela(t, stats) for t in _ordenar(times, stats, jogos_finalizados, usar_divisao=True)]
                for divisao, times in divisoes.items()
            },
            "seeds": seeds[conf],
        }
    return {"formato": "nfl", "conferencias": resultado}


# ----------------------------------------------------------------------
# Playoffs: Wild Card -> Divisional -> Final de Conferência -> Super Bowl
# ----------------------------------------------------------------------

def confrontos_wild_card(seeds: List[str]) -> List[tuple]:
    """seeds[0] = seed 1. O seed 1 folga; mandante é sempre o melhor seed: 2x7, 3x6, 4x5."""
    return [(seeds[1], seeds[6]), (seeds[2], seeds[5]), (seeds[3], seeds[4])]


def confrontos_divisional(seeds: List[str], vencedores_wild_card: List[str]) -> List[tuple]:
    """Reclassifica os 4 que restam: o seed 1 pega o pior seed; os outros dois se enfrentam."""
    restantes = sorted([seeds[0]] + list(vencedores_wild_card), key=seeds.index)
    return [(restantes[0], restantes[-1]), (restantes[1], restantes[2])]


def confronto_final_conferencia(seeds: List[str], vencedores_divisional: List[str]) -> List[tuple]:
    restantes = sorted(vencedores_divisional, key=seeds.index)
    return [(restantes[0], restantes[1])]