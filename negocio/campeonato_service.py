import json
from typing import Optional

from fastapi import HTTPException
from sqlmodel import Session

from acesso_dados.campeonato_repository import (
    salvar_campeonato,
    listar_campeonatos as listar_campeonatos_repo,
    obter_campeonato_por_id,
)
from dados.models import Campeonato


def criar_campeonato(session: Session, nome: str, esporte: str, times: str, criador_id: Optional[int]):
    try:
        lista_times = json.loads(times)
    except Exception:
        raise HTTPException(status_code=400, detail="Times inválidos")

    lista_times = [t.strip() for t in lista_times if t.strip()]

    if len(lista_times) < 2:
        raise HTTPException(status_code=400, detail="Insira ao menos 2 times")

    novo_campeonato = Campeonato(
        nome=nome,
        esporte=esporte,
        quantidade_times=len(lista_times),
        times=json.dumps(lista_times),
        criador_id=criador_id
    )
    novo_campeonato = salvar_campeonato(session, novo_campeonato)

    return {
        "id": novo_campeonato.id,
        "nome": novo_campeonato.nome,
        "esporte": novo_campeonato.esporte,
        "quantidade_times": novo_campeonato.quantidade_times,
        "times": lista_times
    }

def listar_campeonatos(session: Session):
    campeonatos = listar_campeonatos_repo(session)

    return [
        {
            "id": c.id,
            "nome": c.nome,
            "esporte": c.esporte,
            "quantidade_times": c.quantidade_times,
            "times": json.loads(c.times)
        }
        for c in campeonatos
    ]

def obter_campeonato(session: Session, campeonato_id: int):
    campeonato = obter_campeonato_por_id(session, campeonato_id)

    if not campeonato:
        raise HTTPException(status_code=404, detail="Campeonato não encontrado")

    return {
        "id": campeonato.id,
        "nome": campeonato.nome,
        "esporte": campeonato.esporte,
        "quantidade_times": campeonato.quantidade_times,
        "times": json.loads(campeonato.times)
    }
