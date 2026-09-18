import json
import random
from typing import List, Optional

from sqlmodel import Session, select

from dados.models import Campeonato, Partida


def _serializar_partida(partida: Partida) -> dict:
    return {
        "id": partida.id,
        "campeonato_id": partida.campeonato_id,
        "rodada": partida.rodada,
        "turno": partida.turno,
        "time_casa": partida.time_casa,
        "time_visitante": partida.time_visitante,
        "gols_casa": partida.gols_casa,
        "gols_visitante": partida.gols_visitante,
        "finalizada": partida.finalizada,
    }


def _gerar_confrontos_turno(times: List[str]) -> List[List[tuple]]:
    """
    Gera os confrontos de um turno (todos contra todos, uma vez cada)
    usando o método do círculo. Se o número de times for ímpar,
    um time fica de fora (bye) em cada rodada.
    """
    lista = times[:]
    if len(lista) % 2 != 0:
        lista.append(None)  # bye

    n = len(lista)
    rodadas = []

    for _ in range(n - 1):
        confrontos = []
        for i in range(n // 2):
            time_a = lista[i]
            time_b = lista[n - 1 - i]
            if time_a is not None and time_b is not None:
                confrontos.append((time_a, time_b))
        rodadas.append(confrontos)

        # rotaciona todos menos o primeiro time fixo
        lista.insert(1, lista.pop())

    return rodadas


def gerar_partidas(session: Session, campeonato_id: int) -> List[dict]:
    """
    Sorteia os confrontos e gera o calendário completo em turno e returno
    (jogo de ida e volta) para o campeonato. Qualquer partida já existente
    para esse campeonato é apagada e recriada do zero.
    """
    campeonato = session.get(Campeonato, campeonato_id)
    if not campeonato:
        return []

    times = json.loads(campeonato.times)
    if len(times) < 2:
        return []

    times_embaralhados = times[:]
    random.shuffle(times_embaralhados)

    partidas_antigas = session.exec(
        select(Partida).where(Partida.campeonato_id == campeonato_id)
    ).all()
    for partida in partidas_antigas:
        session.delete(partida)
    session.commit()

    rodadas_turno = _gerar_confrontos_turno(times_embaralhados)
    quantidade_rodadas_turno = len(rodadas_turno)

    novas_partidas = []

    # Turno (ida)
    for indice_rodada, confrontos in enumerate(rodadas_turno, start=1):
        for time_casa, time_visitante in confrontos:
            novas_partidas.append(Partida(
                campeonato_id=campeonato_id,
                rodada=indice_rodada,
                turno=1,
                time_casa=time_casa,
                time_visitante=time_visitante,
            ))

    # Returno (volta) - manda quem visitou no turno
    for indice_rodada, confrontos in enumerate(rodadas_turno, start=1):
        for time_casa, time_visitante in confrontos:
            novas_partidas.append(Partida(
                campeonato_id=campeonato_id,
                rodada=quantidade_rodadas_turno + indice_rodada,
                turno=2,
                time_casa=time_visitante,
                time_visitante=time_casa,
            ))

    session.add_all(novas_partidas)
    session.commit()
    for partida in novas_partidas:
        session.refresh(partida)

    return [_serializar_partida(p) for p in novas_partidas]


def listar_partidas(session: Session, campeonato_id: int) -> List[dict]:
    partidas = session.exec(
        select(Partida)
        .where(Partida.campeonato_id == campeonato_id)
        .order_by(Partida.rodada, Partida.id)
    ).all()
    return [_serializar_partida(p) for p in partidas]


def atualizar_resultado(
    session: Session, partida_id: int, gols_casa: int, gols_visitante: int
) -> Optional[dict]:
    partida = session.get(Partida, partida_id)
    if not partida:
        return None

    partida.gols_casa = gols_casa
    partida.gols_visitante = gols_visitante
    partida.finalizada = True

    session.add(partida)
    session.commit()
    session.refresh(partida)

    return _serializar_partida(partida)


def calcular_classificacao(session: Session, campeonato_id: int) -> List[dict]:
    campeonato = session.get(Campeonato, campeonato_id)
    if not campeonato:
        return []

    times = json.loads(campeonato.times)

    tabela = {
        time: {
            "time": time,
            "pontos": 0,
            "jogos": 0,
            "vitorias": 0,
            "empates": 0,
            "derrotas": 0,
            "gols_marcados": 0,
            "gols_sofridos": 0,
            "sequencia": [],  # ordem cronológica: mais antigo -> mais recente
        }
        for time in times
    }

    partidas = session.exec(
        select(Partida)
        .where(Partida.campeonato_id == campeonato_id, Partida.finalizada == True)  # noqa: E712
        .order_by(Partida.rodada, Partida.id)
    ).all()

    for partida in partidas:
        casa = tabela.get(partida.time_casa)
        visitante = tabela.get(partida.time_visitante)
        if not casa or not visitante:
            continue

        casa["jogos"] += 1
        visitante["jogos"] += 1
        casa["gols_marcados"] += partida.gols_casa
        casa["gols_sofridos"] += partida.gols_visitante
        visitante["gols_marcados"] += partida.gols_visitante
        visitante["gols_sofridos"] += partida.gols_casa

        if partida.gols_casa > partida.gols_visitante:
            casa["pontos"] += 3
            casa["vitorias"] += 1
            casa["sequencia"].append("V")
            visitante["derrotas"] += 1
            visitante["sequencia"].append("D")
        elif partida.gols_casa < partida.gols_visitante:
            visitante["pontos"] += 3
            visitante["vitorias"] += 1
            visitante["sequencia"].append("V")
            casa["derrotas"] += 1
            casa["sequencia"].append("D")
        else:
            casa["pontos"] += 1
            visitante["pontos"] += 1
            casa["empates"] += 1
            visitante["empates"] += 1
            casa["sequencia"].append("E")
            visitante["sequencia"].append("E")

    classificacao = []
    for dados_time in tabela.values():
        saldo_gols = dados_time["gols_marcados"] - dados_time["gols_sofridos"]
        classificacao.append({
            "time": dados_time["time"],
            "pontos": dados_time["pontos"],
            "jogos": dados_time["jogos"],
            "vitorias": dados_time["vitorias"],
            "empates": dados_time["empates"],
            "derrotas": dados_time["derrotas"],
            "gols_marcados": dados_time["gols_marcados"],
            "gols_sofridos": dados_time["gols_sofridos"],
            "saldo_gols": saldo_gols,
            "ultimos_5": dados_time["sequencia"][-5:],
        })

    classificacao.sort(key=lambda t: (-t["pontos"], -t["saldo_gols"], -t["gols_marcados"]))

    return classificacao