from typing import Optional

from fastapi import APIRouter, Depends, Form
from sqlmodel import Session

from acesso_dados.database import get_session
from dados.models import Usuario, ResultadoPartida
from negocio.auth_service import obter_usuario_logado
from negocio.campeonato_service import (
    criar_campeonato as _criar_campeonato,
    listar_campeonatos as _listar_campeonatos,
    obter_campeonato as _obter_campeonato,
)
from negocio.partida_service import (
    gerar_partidas as _gerar_partidas,
    listar_partidas as _listar_partidas,
    atualizar_resultado as _atualizar_resultado,
    calcular_classificacao as _calcular_classificacao,
)

router = APIRouter()

# --- API CAMPEONATOS ---

@router.post("/api/campeonatos")
def criar_campeonato(
    nome: str = Form(...),
    esporte: str = Form(...),
    times: str = Form(...),  # JSON string, ex: '["Time A","Time B"]'
    session: Session = Depends(get_session),
    usuario: Optional[Usuario] = Depends(obter_usuario_logado)
):
    return _criar_campeonato(session, nome, esporte, times, usuario.id if usuario else None)

@router.get("/api/campeonatos")
def listar_campeonatos(session: Session = Depends(get_session)):
    return _listar_campeonatos(session)

@router.get("/api/campeonatos/{campeonato_id}")
def obter_campeonato(campeonato_id: int, session: Session = Depends(get_session)):
    return _obter_campeonato(session, campeonato_id)


# --- API PARTIDAS / CLASSIFICAÇÃO ---

@router.post("/api/campeonatos/{campeonato_id}/partidas/gerar")
def gerar_partidas(campeonato_id: int, session: Session = Depends(get_session)):
    """Sorteia o calendário completo (turno e returno) para o campeonato."""
    return _gerar_partidas(session, campeonato_id)

@router.get("/api/campeonatos/{campeonato_id}/partidas")
def listar_partidas(campeonato_id: int, session: Session = Depends(get_session)):
    return _listar_partidas(session, campeonato_id)

@router.put("/api/partidas/{partida_id}/resultado")
def atualizar_resultado(
    partida_id: int,
    resultado: ResultadoPartida,
    session: Session = Depends(get_session)
):
    return _atualizar_resultado(session, partida_id, resultado.gols_casa, resultado.gols_visitante)

@router.get("/api/campeonatos/{campeonato_id}/classificacao")
def obter_classificacao(campeonato_id: int, session: Session = Depends(get_session)):
    return _calcular_classificacao(session, campeonato_id)