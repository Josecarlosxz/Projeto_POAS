import json
import random
from typing import List, Optional, Dict

from fastapi import HTTPException
from sqlmodel import Session, select

from dados.models import Campeonato, Partida, Card

NOMES_GRUPOS_PADRAO = ["A", "B", "C", "D", "E", "F", "G", "H"]
NUM_TIMES_POR_GRUPO = 4  # futebol: grupos sempre com 4 times, top 2 de cada avançam

# Rótulo da fase eliminatória de acordo com a quantidade de partidas naquela rodada
ETAPA_POR_QUANTIDADE_PARTIDAS = {
    8: "Oitavas de Final",
    4: "Quartas de Final",
    2: "Semifinal",
    1: "Final",
}

# Mesma ideia, mas para o mata-mata restrito a uma conferência (basquete),
# pra não confundir com a Final de verdade (entre os campeões de conferência)
ETAPA_CONFERENCIA_POR_QUANTIDADE_PARTIDAS = {
    4: "Quartas de Final de Conferência",
    2: "Semifinal de Conferência",
    1: "Final de Conferência",
}


def _etapa_para_quantidade_partidas(quantidade_partidas: int) -> str:
    return ETAPA_POR_QUANTIDADE_PARTIDAS.get(quantidade_partidas, f"Fase de {quantidade_partidas * 2}")


def _etapa_conferencia_para_quantidade_partidas(quantidade_partidas: int) -> str:
    return ETAPA_CONFERENCIA_POR_QUANTIDADE_PARTIDAS.get(quantidade_partidas, f"Fase de Conferência ({quantidade_partidas * 2})")


# ----------------------------------------------------------------------
# Helpers gerais
# ----------------------------------------------------------------------

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
        "fase": partida.fase,
        "grupo": partida.grupo,
        "conferencia": partida.conferencia,
        "divisao": partida.divisao,
        "etapa": partida.etapa,
        "categoria": partida.categoria,
        "metodo_vitoria": partida.metodo_vitoria,
        "vencedor_penaltis": partida.vencedor_penaltis,
        "card_id": partida.card_id,
    }


def _obter_configuracao(campeonato: Campeonato) -> dict:
    if not campeonato.configuracao:
        return {}
    try:
        return json.loads(campeonato.configuracao)
    except Exception:
        return {}


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


def _gerar_partidas_rodada_unica_ou_dupla(
    times: List[str],
    campeonato_id: int,
    ida_volta: bool,
    fase: Optional[str] = None,
    grupo: Optional[str] = None,
    conferencia: Optional[str] = None,
    categoria: Optional[str] = None,
) -> List[Partida]:
    """
    Motor genérico de rodadas: sorteia todos-contra-todos uma vez (turno) e,
    se ida_volta=True, também o returno (mandantes invertidos). Usado tanto
    pela temporada regular quanto pela fase de grupos (futebol) e pela
    temporada por conferência (basquete) - as tags fase/grupo/conferencia
    dizem a que parte do campeonato aquelas partidas pertencem.
    """
    times_embaralhados = times[:]
    random.shuffle(times_embaralhados)

    rodadas_turno = _gerar_confrontos_turno(times_embaralhados)
    quantidade_rodadas_turno = len(rodadas_turno)

    partidas = []

    for indice_rodada, confrontos in enumerate(rodadas_turno, start=1):
        for time_casa, time_visitante in confrontos:
            partidas.append(Partida(
                campeonato_id=campeonato_id,
                rodada=indice_rodada,
                turno=1,
                time_casa=time_casa,
                time_visitante=time_visitante,
                fase=fase,
                grupo=grupo,
                conferencia=conferencia,
                categoria=categoria,
            ))

    if ida_volta:
        for indice_rodada, confrontos in enumerate(rodadas_turno, start=1):
            for time_casa, time_visitante in confrontos:
                partidas.append(Partida(
                    campeonato_id=campeonato_id,
                    rodada=quantidade_rodadas_turno + indice_rodada,
                    turno=2,
                    time_casa=time_visitante,
                    time_visitante=time_casa,
                    fase=fase,
                    grupo=grupo,
                    conferencia=conferencia,
                    categoria=categoria,
                ))

    return partidas


def _maior_potencia_de_dois_ate(valor: int, teto: int) -> int:
    n = 1
    while n * 2 <= min(valor, teto):
        n *= 2
    return n


def _parear_seed_classico(times_ordenados: List[str]) -> List[tuple]:
    """Seed clássico de chaveamento: melhor x pior, 2º melhor x 2º pior, etc."""
    n = len(times_ordenados)
    return [(times_ordenados[i], times_ordenados[n - 1 - i]) for i in range(n // 2)]


def _vencedor_partida(partida: Partida) -> str:
    if partida.gols_casa > partida.gols_visitante:
        return partida.time_casa
    if partida.gols_visitante > partida.gols_casa:
        return partida.time_visitante
    if partida.vencedor_penaltis in (partida.time_casa, partida.time_visitante):
        return partida.vencedor_penaltis
    raise HTTPException(
        status_code=400,
        detail=f"A partida {partida.time_casa} x {partida.time_visitante} terminou empatada. "
               f"Informe o vencedor nos pênaltis para avançar de fase."
    )


# ----------------------------------------------------------------------
# Futebol - fase de grupos (validação e divisão)
# ----------------------------------------------------------------------

def calcular_num_grupos(quantidade_times: int) -> int:
    """Cada grupo tem sempre 4 times. Levanta erro se a quantidade não permitir isso."""
    if quantidade_times % NUM_TIMES_POR_GRUPO != 0:
        raise HTTPException(
            status_code=400,
            detail=f"Para a fase de grupos + playoffs, a quantidade de times precisa ser múltipla de {NUM_TIMES_POR_GRUPO}"
        )
    num_grupos = quantidade_times // NUM_TIMES_POR_GRUPO
    # precisa ser potência de 2 para o mata-mata fechar sem "bye" (2, 4 ou 8 grupos)
    if num_grupos & (num_grupos - 1) != 0:
        raise HTTPException(
            status_code=400,
            detail="Para a fase de grupos + playoffs, o número de grupos de 4 times precisa ser 2, 4 ou 8 "
                    "(ou seja, 8, 16 ou 32 times no total)"
        )
    return num_grupos


def _dividir_em_grupos(times: List[str]) -> Dict[str, List[str]]:
    """Distribui os times (já embaralhados) em grupos de 4, em blocos sequenciais."""
    num_grupos = calcular_num_grupos(len(times))
    grupos: Dict[str, List[str]] = {}
    for i in range(num_grupos):
        nome_grupo = NOMES_GRUPOS_PADRAO[i]
        grupos[nome_grupo] = times[i * NUM_TIMES_POR_GRUPO: (i + 1) * NUM_TIMES_POR_GRUPO]
    return grupos


# ----------------------------------------------------------------------
# Tabelas de classificação
# ----------------------------------------------------------------------

def _calcular_tabela_pontos_corridos(times: List[str], partidas: List[Partida]) -> List[dict]:
    """Tabela estilo futebol: 3 pontos por vitória, 1 por empate."""
    tabela = {
        time: {
            "time": time, "pontos": 0, "jogos": 0, "vitorias": 0, "empates": 0, "derrotas": 0,
            "gols_marcados": 0, "gols_sofridos": 0, "sequencia": [],
        }
        for time in times
    }

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
    for d in tabela.values():
        saldo_gols = d["gols_marcados"] - d["gols_sofridos"]
        classificacao.append({
            "time": d["time"], "pontos": d["pontos"], "jogos": d["jogos"], "vitorias": d["vitorias"],
            "empates": d["empates"], "derrotas": d["derrotas"], "gols_marcados": d["gols_marcados"],
            "gols_sofridos": d["gols_sofridos"], "saldo_gols": saldo_gols, "ultimos_5": d["sequencia"][-5:],
        })

    classificacao.sort(key=lambda t: (-t["pontos"], -t["saldo_gols"], -t["gols_marcados"]))
    return classificacao


def _calcular_tabela_basquete(times: List[str], partidas: List[Partida]) -> List[dict]:
    """Tabela estilo NBA: sem empate possível, ordenada por número de vitórias."""
    tabela = {
        time: {
            "time": time, "jogos": 0, "vitorias": 0, "derrotas": 0,
            "pontos_marcados": 0, "pontos_sofridos": 0, "sequencia": [],
        }
        for time in times
    }

    for partida in partidas:
        casa = tabela.get(partida.time_casa)
        visitante = tabela.get(partida.time_visitante)
        if not casa or not visitante:
            continue

        casa["jogos"] += 1
        visitante["jogos"] += 1
        casa["pontos_marcados"] += partida.gols_casa
        casa["pontos_sofridos"] += partida.gols_visitante
        visitante["pontos_marcados"] += partida.gols_visitante
        visitante["pontos_sofridos"] += partida.gols_casa

        if partida.gols_casa > partida.gols_visitante:
            casa["vitorias"] += 1
            casa["sequencia"].append("V")
            visitante["derrotas"] += 1
            visitante["sequencia"].append("D")
        else:
            visitante["vitorias"] += 1
            visitante["sequencia"].append("V")
            casa["derrotas"] += 1
            casa["sequencia"].append("D")

    classificacao = []
    for d in tabela.values():
        saldo_pontos = d["pontos_marcados"] - d["pontos_sofridos"]
        aproveitamento = round((d["vitorias"] / d["jogos"]) * 100, 1) if d["jogos"] > 0 else 0.0
        classificacao.append({
            "time": d["time"], "jogos": d["jogos"], "vitorias": d["vitorias"], "derrotas": d["derrotas"],
            "pontos_marcados": d["pontos_marcados"], "pontos_sofridos": d["pontos_sofridos"],
            "saldo_pontos": saldo_pontos, "aproveitamento": aproveitamento, "ultimos_5": d["sequencia"][-5:],
        })

    classificacao.sort(key=lambda t: (-t["vitorias"], -t["saldo_pontos"], -t["pontos_marcados"]))
    return classificacao


# ----------------------------------------------------------------------
# Geração de partidas (temporada regular)
# ----------------------------------------------------------------------

def gerar_partidas(session: Session, campeonato_id: int) -> List[dict]:
    """
    Sorteia os confrontos da temporada regular, de acordo com o esporte e a
    configuração do campeonato. Qualquer partida já existente é apagada e
    recriada do zero (incluindo playoffs).
    """
    campeonato = session.get(Campeonato, campeonato_id)
    if not campeonato:
        return []

    times = json.loads(campeonato.times)
    if len(times) < 2:
        return []

    configuracao = _obter_configuracao(campeonato)

    if campeonato.esporte == "UFC":
        raise HTTPException(
            status_code=400,
            detail="No UFC as lutas são marcadas manualmente, uma a uma, dentro de cada categoria"
        )

    partidas_antigas = session.exec(
        select(Partida).where(Partida.campeonato_id == campeonato_id)
    ).all()
    for partida in partidas_antigas:
        session.delete(partida)
    session.commit()

    novas_partidas: List[Partida] = []

    if campeonato.esporte == "Futebol":
        formato = configuracao.get("formato", "pontos_corridos")
        if formato == "grupos_playoffs":
            calcular_num_grupos(len(times))
            times_embaralhados = times[:]
            random.shuffle(times_embaralhados)
            grupos = _dividir_em_grupos(times_embaralhados)
            ida_volta_grupos = configuracao.get("turno_grupos") == "ida_volta"
            for nome_grupo, times_do_grupo in grupos.items():
                novas_partidas += _gerar_partidas_rodada_unica_ou_dupla(
                    times_do_grupo, campeonato_id, ida_volta_grupos, fase="grupos", grupo=nome_grupo
                )
        else:
            novas_partidas = _gerar_partidas_rodada_unica_ou_dupla(times, campeonato_id, True)

    elif campeonato.esporte == "Basquete":
        # O usuário já definiu o nome de cada conferência e seus times na criação
        # (1 ou 2 conferências); não há mais sorteio automático de quem vai pra onde.
        conferencias_dict = configuracao.get("conferencias", {})
        ida_volta_temporada = configuracao.get("turno_temporada", "unico") == "ida_volta"
        for nome_conf, times_da_conf in conferencias_dict.items():
            novas_partidas += _gerar_partidas_rodada_unica_ou_dupla(
                times_da_conf, campeonato_id, ida_volta_temporada, conferencia=nome_conf
            )

    else:
        # esportes ainda não configuráveis (NFL, F1) - comportamento padrão por enquanto
        novas_partidas = _gerar_partidas_rodada_unica_ou_dupla(times, campeonato_id, True)

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
    session: Session,
    partida_id: int,
    gols_casa: int,
    gols_visitante: int,
    vencedor_penaltis: Optional[str] = None,
) -> Optional[dict]:
    partida = session.get(Partida, partida_id)
    if not partida:
        return None

    campeonato = session.get(Campeonato, partida.campeonato_id)
    if campeonato and campeonato.esporte == "Basquete" and gols_casa == gols_visitante:
        raise HTTPException(status_code=400, detail="Basquete não permite empate — o placar não pode terminar igual")

    partida.gols_casa = gols_casa
    partida.gols_visitante = gols_visitante
    partida.finalizada = True
    if vencedor_penaltis:
        partida.vencedor_penaltis = vencedor_penaltis

    session.add(partida)
    session.commit()
    session.refresh(partida)

    return _serializar_partida(partida)


METODOS_VITORIA_VALIDOS = {"KO", "TKO", "SUB", "DEC"}


def atualizar_resultado_luta(session: Session, partida_id: int, vencedor: str, metodo: str) -> Optional[dict]:
    """UFC: registra o vencedor e o método (KO/TKO/SUB/DEC) de uma luta."""
    partida = session.get(Partida, partida_id)
    if not partida:
        return None

    if vencedor not in (partida.time_casa, partida.time_visitante):
        raise HTTPException(status_code=400, detail="O vencedor precisa ser um dos dois lutadores da luta")
    if metodo not in METODOS_VITORIA_VALIDOS:
        raise HTTPException(status_code=400, detail="Método de vitória inválido (use KO, TKO, SUB ou DEC)")

    partida.gols_casa = 1 if vencedor == partida.time_casa else 0
    partida.gols_visitante = 1 if vencedor == partida.time_visitante else 0
    partida.metodo_vitoria = metodo
    partida.finalizada = True

    session.add(partida)
    session.commit()
    session.refresh(partida)

    return _serializar_partida(partida)


def _serializar_card(card: Card) -> dict:
    return {"id": card.id, "campeonato_id": card.campeonato_id, "nome": card.nome}


def _obter_campeonato_ufc(session: Session, campeonato_id: int) -> Campeonato:
    campeonato = session.get(Campeonato, campeonato_id)
    if not campeonato:
        raise HTTPException(status_code=404, detail="Campeonato não encontrado")
    if campeonato.esporte != "UFC":
        raise HTTPException(status_code=400, detail="Cards só existem em campeonatos de UFC")
    return campeonato


def listar_cards(session: Session, campeonato_id: int) -> List[dict]:
    cards = session.exec(
        select(Card).where(Card.campeonato_id == campeonato_id).order_by(Card.id)
    ).all()
    return [_serializar_card(c) for c in cards]


def criar_card(session: Session, campeonato_id: int, nome: str) -> dict:
    """UFC: cria um card (evento) com o nome escolhido pelo usuário. As lutas são adicionadas dentro dele."""
    _obter_campeonato_ufc(session, campeonato_id)

    nome = (nome or "").strip()
    if not nome:
        raise HTTPException(status_code=400, detail="Dê um nome ao card")

    existentes = session.exec(select(Card).where(Card.campeonato_id == campeonato_id)).all()
    if any(c.nome.lower() == nome.lower() for c in existentes):
        raise HTTPException(status_code=400, detail=f"Já existe um card chamado '{nome}' nesse campeonato")

    card = Card(campeonato_id=campeonato_id, nome=nome)
    session.add(card)
    session.commit()
    session.refresh(card)
    return _serializar_card(card)


def remover_card(session: Session, card_id: int) -> dict:
    """UFC: remove o card e as lutas pendentes dele (só se nenhuma luta do card tiver resultado)."""
    card = session.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card não encontrado")
    _obter_campeonato_ufc(session, card.campeonato_id)

    lutas = session.exec(select(Partida).where(Partida.card_id == card_id)).all()
    if any(l.finalizada for l in lutas):
        raise HTTPException(status_code=400, detail="Não é possível remover um card que já tem lutas com resultado")

    for luta in lutas:
        session.delete(luta)
    session.delete(card)
    session.commit()
    return {"removido": True}


def criar_luta(
    session: Session,
    card_id: int,
    categoria: str,
    lutador_casa: str,
    lutador_visitante: str,
    titulo: bool = False,
) -> dict:
    """UFC: adiciona uma luta (normal ou pelo cinturão) a um card, escolhendo os dois lutadores."""
    card = session.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card não encontrado")
    campeonato = _obter_campeonato_ufc(session, card.campeonato_id)
    campeonato_id = campeonato.id

    configuracao = _obter_configuracao(campeonato)
    lutadores_validos = configuracao.get("categorias", {}).get(categoria)
    if lutadores_validos is None:
        raise HTTPException(status_code=400, detail=f"Categoria '{categoria}' não encontrada nesse campeonato")

    if lutador_casa == lutador_visitante:
        raise HTTPException(status_code=400, detail="Escolha dois lutadores diferentes")
    if lutador_casa not in lutadores_validos or lutador_visitante not in lutadores_validos:
        raise HTTPException(status_code=400, detail="Os dois lutadores precisam pertencer à categoria escolhida")

    # um lutador não luta duas vezes no mesmo card
    lutas_do_card = session.exec(select(Partida).where(Partida.card_id == card_id)).all()
    ocupados = {l.time_casa for l in lutas_do_card} | {l.time_visitante for l in lutas_do_card}
    for lutador in (lutador_casa, lutador_visitante):
        if lutador in ocupados:
            raise HTTPException(status_code=400, detail=f"{lutador} já tem luta nesse card")

    if titulo:
        luta_titulo_pendente = session.exec(
            select(Partida).where(
                Partida.campeonato_id == campeonato_id,
                Partida.categoria == categoria,
                Partida.fase == "titulo",
                Partida.finalizada == False,  # noqa: E712
            )
        ).first()
        if luta_titulo_pendente:
            raise HTTPException(
                status_code=400,
                detail="Já existe uma luta de título pendente nessa categoria. Registre o resultado antes de marcar outra."
            )

    # rodada = id do card: mantém a ordem cronológica dos cards (usada pra achar o campeão mais recente)
    nova_luta = Partida(
        campeonato_id=campeonato_id, rodada=card.id, turno=1,
        time_casa=lutador_casa, time_visitante=lutador_visitante,
        fase="titulo" if titulo else None,
        categoria=categoria,
        etapa="Luta pelo Cinturão" if titulo else None,
        card_id=card.id,
    )
    session.add(nova_luta)
    session.commit()
    session.refresh(nova_luta)

    return _serializar_partida(nova_luta)


def remover_luta(session: Session, partida_id: int) -> dict:
    """UFC: desfaz uma luta marcada por engano (só enquanto ainda não tem resultado)."""
    partida = session.get(Partida, partida_id)
    if not partida:
        raise HTTPException(status_code=404, detail="Luta não encontrada")

    campeonato = session.get(Campeonato, partida.campeonato_id)
    if not campeonato or campeonato.esporte != "UFC":
        raise HTTPException(status_code=400, detail="Só é possível remover lutas de campeonatos de UFC")
    if partida.finalizada:
        raise HTTPException(status_code=400, detail="Não é possível remover uma luta que já tem resultado")

    session.delete(partida)
    session.commit()
    return {"removida": True}


def _calcular_situacao_titulo(lutas_titulo_em_ordem: List[Partida]) -> tuple:
    """
    Percorre as lutas de título já finalizadas (da mais antiga pra mais recente) e devolve
    (campeão atual, ex-campeão). O ex-campeão é quem acabou de perder o cinturão: ele volta
    ao ranking como número 1. Defesa de título bem-sucedida não muda nada.
    """
    campeao: Optional[str] = None
    ex_campeao: Optional[str] = None
    for luta in lutas_titulo_em_ordem:
        vencedor = _vencedor_partida(luta)
        if campeao is not None and vencedor != campeao:
            ex_campeao = campeao
        campeao = vencedor
    return campeao, ex_campeao


def _situacao_titulo_categoria(session: Session, campeonato_id: int, categoria: str) -> tuple:
    lutas_titulo = session.exec(
        select(Partida).where(
            Partida.campeonato_id == campeonato_id,
            Partida.categoria == categoria,
            Partida.fase == "titulo",
            Partida.finalizada == True,  # noqa: E712
        ).order_by(Partida.rodada, Partida.id)
    ).all()
    return _calcular_situacao_titulo(lutas_titulo)


def _montar_ranking(tabela: List[dict], campeao: Optional[str], ex_campeao: Optional[str]) -> List[dict]:
    """
    Ranking dos desafiantes: o campeão sai da lista (quem era 2º sobe pra 1º) e o ex-campeão,
    se houver, volta como número 1. Os demais seguem a ordem de vitórias da tabela.
    """
    ranking = [linha for linha in tabela if linha["time"] != campeao]
    if ex_campeao is not None:
        ranking.sort(key=lambda linha: linha["time"] != ex_campeao)  # sort estável: só puxa o ex-campeão pro topo
    return ranking


# ----------------------------------------------------------------------
# Classificação
# ----------------------------------------------------------------------

def calcular_classificacao(session: Session, campeonato_id: int) -> dict:
    campeonato = session.get(Campeonato, campeonato_id)
    if not campeonato:
        return {"formato": "pontos_corridos", "classificacao": []}

    times = json.loads(campeonato.times)
    configuracao = _obter_configuracao(campeonato)

    if campeonato.esporte == "Futebol":
        formato = configuracao.get("formato", "pontos_corridos")

        if formato == "grupos_playoffs":
            partidas_grupos = session.exec(
                select(Partida).where(Partida.campeonato_id == campeonato_id, Partida.fase == "grupos")
            ).all()

            grupos_times: Dict[str, set] = {}
            for partida in partidas_grupos:
                grupos_times.setdefault(partida.grupo, set()).add(partida.time_casa)
                grupos_times.setdefault(partida.grupo, set()).add(partida.time_visitante)

            resultado_grupos = {}
            for nome_grupo, times_do_grupo in sorted(grupos_times.items()):
                finalizadas = [p for p in partidas_grupos if p.grupo == nome_grupo and p.finalizada]
                resultado_grupos[nome_grupo] = _calcular_tabela_pontos_corridos(list(times_do_grupo), finalizadas)

            return {"formato": "grupos_playoffs", "grupos": resultado_grupos}

        partidas = session.exec(
            select(Partida)
            .where(Partida.campeonato_id == campeonato_id, Partida.finalizada == True, Partida.fase == None)  # noqa: E711,E712
            .order_by(Partida.rodada, Partida.id)
        ).all()
        return {"formato": "pontos_corridos", "classificacao": _calcular_tabela_pontos_corridos(times, partidas)}

    if campeonato.esporte == "Basquete":
        conferencias_dict = configuracao.get("conferencias", {})

        partidas_temporada = session.exec(
            select(Partida).where(Partida.campeonato_id == campeonato_id, Partida.fase == None)  # noqa: E711
        ).all()

        resultado_conf = {}
        for nome_conf, times_da_conf in conferencias_dict.items():
            finalizadas = [p for p in partidas_temporada if p.conferencia == nome_conf and p.finalizada]
            resultado_conf[nome_conf] = _calcular_tabela_basquete(times_da_conf, finalizadas)

        return {"formato": "conferencias", "conferencias": resultado_conf}

    if campeonato.esporte == "UFC":
        categorias_dict = configuracao.get("categorias", {})

        # Todas as lutas finalizadas entram na tabela (normais e de cinturão): quem perde o
        # cinturão também ganha a derrota, e quem o conquista ganha a vitória.
        todas_as_lutas = session.exec(
            select(Partida).where(Partida.campeonato_id == campeonato_id)
        ).all()

        resultado_categorias = {}
        for nome_categoria, lutadores in categorias_dict.items():
            finalizadas = [p for p in todas_as_lutas if p.categoria == nome_categoria and p.finalizada]
            campeao, ex_campeao = _situacao_titulo_categoria(session, campeonato_id, nome_categoria)
            tabela = _calcular_tabela_basquete(lutadores, finalizadas)
            resultado_categorias[nome_categoria] = {
                "tabela": _montar_ranking(tabela, campeao, ex_campeao),
                "campeao": campeao,
            }

        return {"formato": "categorias", "categorias": resultado_categorias}

    # esportes ainda não configuráveis - fallback antigo
    partidas = session.exec(
        select(Partida)
        .where(Partida.campeonato_id == campeonato_id, Partida.finalizada == True, Partida.fase == None)  # noqa: E711,E712
        .order_by(Partida.rodada, Partida.id)
    ).all()
    return {"formato": "pontos_corridos", "classificacao": _calcular_tabela_pontos_corridos(times, partidas)}


# ----------------------------------------------------------------------
# Playoffs (mata-mata) - despachantes por esporte
# ----------------------------------------------------------------------

def gerar_playoffs(session: Session, campeonato_id: int) -> List[dict]:
    campeonato = session.get(Campeonato, campeonato_id)
    if not campeonato:
        raise HTTPException(status_code=404, detail="Campeonato não encontrado")

    if campeonato.esporte == "Futebol":
        return _gerar_playoffs_futebol(session, campeonato_id)
    if campeonato.esporte == "Basquete":
        return _gerar_playoffs_basquete(session, campeonato_id)

    raise HTTPException(status_code=400, detail="Playoffs ainda não estão disponíveis para este esporte")


def avancar_fase_playoffs(session: Session, campeonato_id: int) -> dict:
    campeonato = session.get(Campeonato, campeonato_id)
    if not campeonato:
        raise HTTPException(status_code=404, detail="Campeonato não encontrado")

    if campeonato.esporte == "Futebol":
        return _avancar_fase_playoffs_generico(session, campeonato_id)

    if campeonato.esporte == "Basquete":
        configuracao = _obter_configuracao(campeonato)
        if len(configuracao.get("conferencias", {})) == 2:
            return _avancar_fase_playoffs_basquete_conferencias(session, campeonato_id)
        return _avancar_fase_playoffs_generico(session, campeonato_id)

    raise HTTPException(status_code=400, detail="Playoffs ainda não estão disponíveis para este esporte")


# --- Futebol: grupos -> mata-mata único (cruzando grupos) ---

def _gerar_playoffs_futebol(session: Session, campeonato_id: int) -> List[dict]:
    campeonato = session.get(Campeonato, campeonato_id)
    configuracao = _obter_configuracao(campeonato)
    if configuracao.get("formato") != "grupos_playoffs":
        raise HTTPException(status_code=400, detail="Este campeonato não usa o formato de grupos + playoffs")

    partidas_grupos = session.exec(
        select(Partida).where(Partida.campeonato_id == campeonato_id, Partida.fase == "grupos")
    ).all()

    if not partidas_grupos:
        raise HTTPException(status_code=400, detail="Sorteie a fase de grupos antes de gerar os playoffs")
    if any(not p.finalizada for p in partidas_grupos):
        raise HTTPException(status_code=400, detail="Ainda há partidas da fase de grupos sem resultado")

    classificacao = calcular_classificacao(session, campeonato_id)["grupos"]
    nomes_grupos = sorted(classificacao.keys())
    num_grupos = len(nomes_grupos)

    if num_grupos < 2 or (num_grupos & (num_grupos - 1) != 0):
        raise HTTPException(status_code=400, detail="Geração automática de playoffs só está disponível para 2, 4 ou 8 grupos")

    primeiros = [classificacao[g][0]["time"] for g in nomes_grupos]
    segundos = [classificacao[g][1]["time"] for g in nomes_grupos]

    playoffs_antigos = session.exec(
        select(Partida).where(Partida.campeonato_id == campeonato_id, Partida.fase == "playoffs")
    ).all()
    for p in playoffs_antigos:
        session.delete(p)
    session.commit()

    confrontos = [(primeiros[i], segundos[(i + 1) % num_grupos]) for i in range(num_grupos)]
    etapa_inicial = _etapa_para_quantidade_partidas(len(confrontos))

    novas_partidas = [
        Partida(
            campeonato_id=campeonato_id, rodada=1, turno=1,
            time_casa=casa, time_visitante=visitante, fase="playoffs", etapa=etapa_inicial,
        )
        for casa, visitante in confrontos
    ]

    session.add_all(novas_partidas)
    session.commit()
    for p in novas_partidas:
        session.refresh(p)
    return [_serializar_partida(p) for p in novas_partidas]


# --- Genérico: um único bracket até a Final (futebol e basquete de 1 conferência) ---

def _avancar_fase_playoffs_generico(session: Session, campeonato_id: int) -> dict:
    partidas_playoffs = session.exec(
        select(Partida)
        .where(Partida.campeonato_id == campeonato_id, Partida.fase == "playoffs")
        .order_by(Partida.rodada, Partida.id)
    ).all()

    if not partidas_playoffs:
        raise HTTPException(status_code=400, detail="Gere os playoffs antes de avançar de fase")

    rodada_atual = max(p.rodada for p in partidas_playoffs)
    partidas_rodada_atual = [p for p in partidas_playoffs if p.rodada == rodada_atual]

    if any(not p.finalizada for p in partidas_rodada_atual):
        raise HTTPException(status_code=400, detail="Ainda há partidas dessa fase sem resultado")

    if len(partidas_rodada_atual) == 1:
        campeao = _vencedor_partida(partidas_rodada_atual[0])
        return {"finalizado": True, "campeao": campeao, "partidas": []}

    vencedores = [_vencedor_partida(p) for p in partidas_rodada_atual]
    proxima_etapa = _etapa_para_quantidade_partidas(len(vencedores) // 2)

    novas_partidas = []
    for i in range(0, len(vencedores), 2):
        if i + 1 >= len(vencedores):
            break
        novas_partidas.append(Partida(
            campeonato_id=campeonato_id, rodada=rodada_atual + 1, turno=1,
            time_casa=vencedores[i], time_visitante=vencedores[i + 1],
            fase="playoffs", etapa=proxima_etapa,
        ))

    session.add_all(novas_partidas)
    session.commit()
    for p in novas_partidas:
        session.refresh(p)
    return {"finalizado": False, "campeao": None, "partidas": [_serializar_partida(p) for p in novas_partidas]}


# --- Basquete: playoffs (1 ou 2 conferências) ---

def _gerar_playoffs_basquete(session: Session, campeonato_id: int) -> List[dict]:
    classificacao = calcular_classificacao(session, campeonato_id)
    nomes_conf = sorted(classificacao["conferencias"].keys())

    if not nomes_conf:
        raise HTTPException(status_code=400, detail="Configuração de conferências inválida")

    playoffs_antigos = session.exec(
        select(Partida).where(Partida.campeonato_id == campeonato_id, Partida.fase == "playoffs")
    ).all()
    for p in playoffs_antigos:
        session.delete(p)
    session.commit()

    # Com 2 conferências, cada uma leva o top 4 pro próprio mata-mata (estilo NBA);
    # com 1 conferência só, é um único chaveamento com o top 8.
    teto_por_bracket = 4 if len(nomes_conf) == 2 else 8

    novas_partidas: List[Partida] = []

    for nome_conf in nomes_conf:
        tabela = classificacao["conferencias"][nome_conf]
        if not tabela or any(t["jogos"] == 0 for t in tabela):
            raise HTTPException(status_code=400, detail=f"A temporada da conferência {nome_conf} ainda não terminou")

        tamanho = _maior_potencia_de_dois_ate(len(tabela), teto_por_bracket)
        if tamanho < 2:
            raise HTTPException(status_code=400, detail=f"A conferência {nome_conf} não tem times suficientes para playoffs")

        top = [t["time"] for t in tabela[:tamanho]]
        confrontos = _parear_seed_classico(top)
        etapa = (
            _etapa_conferencia_para_quantidade_partidas(len(confrontos))
            if len(nomes_conf) == 2
            else _etapa_para_quantidade_partidas(len(confrontos))
        )

        for casa, visitante in confrontos:
            novas_partidas.append(Partida(
                campeonato_id=campeonato_id, rodada=1, turno=1,
                time_casa=casa, time_visitante=visitante,
                fase="playoffs", conferencia=nome_conf, etapa=etapa,
            ))

    session.add_all(novas_partidas)
    session.commit()
    for p in novas_partidas:
        session.refresh(p)
    return [_serializar_partida(p) for p in novas_partidas]


def _avancar_fase_playoffs_basquete_conferencias(session: Session, campeonato_id: int) -> dict:
    todas = session.exec(
        select(Partida)
        .where(Partida.campeonato_id == campeonato_id, Partida.fase == "playoffs")
        .order_by(Partida.rodada, Partida.id)
    ).all()

    if not todas:
        raise HTTPException(status_code=400, detail="Gere os playoffs antes de avançar de fase")

    partida_final = next((p for p in todas if p.conferencia is None), None)
    if partida_final:
        if not partida_final.finalizada:
            raise HTTPException(status_code=400, detail="A Final ainda não tem resultado")
        campeao = _vencedor_partida(partida_final)
        return {"finalizado": True, "campeao": campeao, "partidas": []}

    partidas_por_conf: Dict[str, List[Partida]] = {}
    for p in todas:
        partidas_por_conf.setdefault(p.conferencia, []).append(p)

    nomes_conf = sorted(partidas_por_conf.keys())
    if len(nomes_conf) != 2:
        raise HTTPException(status_code=400, detail="Configuração de playoffs de conferência inválida")

    novas_partidas = []
    campeoes_conferencia: Dict[str, str] = {}

    for nome_conf in nomes_conf:
        partidas_conf = partidas_por_conf[nome_conf]
        rodada_atual = max(p.rodada for p in partidas_conf)
        partidas_rodada_atual = [p for p in partidas_conf if p.rodada == rodada_atual]

        if any(not p.finalizada for p in partidas_rodada_atual):
            raise HTTPException(status_code=400, detail=f"Ainda há jogos pendentes na Conferência {nome_conf}")

        if len(partidas_rodada_atual) == 1:
            campeoes_conferencia[nome_conf] = _vencedor_partida(partidas_rodada_atual[0])
            continue

        vencedores = [_vencedor_partida(p) for p in partidas_rodada_atual]
        proxima_etapa = _etapa_conferencia_para_quantidade_partidas(len(vencedores) // 2)
        for i in range(0, len(vencedores), 2):
            novas_partidas.append(Partida(
                campeonato_id=campeonato_id, rodada=rodada_atual + 1, turno=1,
                time_casa=vencedores[i], time_visitante=vencedores[i + 1],
                fase="playoffs", conferencia=nome_conf, etapa=proxima_etapa,
            ))

    if novas_partidas:
        session.add_all(novas_partidas)
        session.commit()
        for p in novas_partidas:
            session.refresh(p)
        return {"finalizado": False, "campeao": None, "partidas": [_serializar_partida(p) for p in novas_partidas]}

    if len(campeoes_conferencia) == 2:
        maior_rodada = max(p.rodada for p in todas)
        nome_a, nome_b = nomes_conf
        nova_final = Partida(
            campeonato_id=campeonato_id, rodada=maior_rodada + 1, turno=1,
            time_casa=campeoes_conferencia[nome_a], time_visitante=campeoes_conferencia[nome_b],
            fase="playoffs", conferencia=None, etapa="Final",
        )
        session.add(nova_final)
        session.commit()
        session.refresh(nova_final)
        return {"finalizado": False, "campeao": None, "partidas": [_serializar_partida(nova_final)]}

    raise HTTPException(status_code=400, detail="Estado inesperado dos playoffs")