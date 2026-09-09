import json
from typing import List, Optional

from sqlmodel import Session

from domain.entities.campeonato import Campeonato
from infrastructure.repositories.campeonato_repository_sql import CampeonatoRepositorySQL


def _serializar(campeonato: Campeonato) -> dict:
    return {
        "id": campeonato.id,
        "nome": campeonato.nome,
        "esporte": campeonato.esporte,
        "quantidade_times": campeonato.quantidade_times,
        "times": json.loads(campeonato.times),
    }


def criar_campeonato(
    session: Session,
    nome: str,
    esporte: str,
    times_json: str,
    criador_id: Optional[int],
) -> dict:
    try:
        lista_times = json.loads(times_json)
    except Exception:
        raise ValueError("Times inválidos")

    lista_times = [t.strip() for t in lista_times if t.strip()]

    if len(lista_times) < 2:
        raise ValueError("Insira ao menos 2 times")

    novo_campeonato = Campeonato(
        nome=nome,
        esporte=esporte,
        quantidade_times=len(lista_times),
        times=json.dumps(lista_times),
        criador_id=criador_id,
    )

    repo = CampeonatoRepositorySQL(session)
    novo_campeonato = repo.salvar(novo_campeonato)

    return {
        "id": novo_campeonato.id,
        "nome": novo_campeonato.nome,
        "esporte": novo_campeonato.esporte,
        "quantidade_times": novo_campeonato.quantidade_times,
        "times": lista_times,
    }


def listar_campeonatos(session: Session) -> List[dict]:
    repo = CampeonatoRepositorySQL(session)
    return [_serializar(c) for c in repo.listar_todos()]


def obter_campeonato(session: Session, campeonato_id: int) -> dict:
    repo = CampeonatoRepositorySQL(session)
    campeonato = repo.buscar_por_id(campeonato_id)

    if not campeonato:
        raise LookupError("Campeonato não encontrado")

    return _serializar(campeonato)
