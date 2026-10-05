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
    gerar_playoffs as _gerar_playoffs,
    avancar_fase_playoffs as _avancar_fase_playoffs,
)

router = APIRouter()

# --- API CAMPEONATOS ---

@router.post("/api/campeonatos")
def criar_campeonato(
    nome: str = Form(...),
    esporte: str = Form(...),
    times: str = Form(...),  # JSON string, ex: '["Time A","Time B"]'
    configuracao: Optional[str] = Form(None),  # JSON string, ex: '{"formato":"grupos_playoffs"}'
    session: Session = Depends(get_session),
    usuario: Optional[Usuario] = Depends(obter_usuario_logado)
):
    return _criar_campeonato(session, nome, esporte, times, usuario.id if usuario else None, configuracao)

@router.get("/api/campeonatos")
def listar_campeonatos(session: Session = Depends(get_session)):
    return _listar_campeonatos(session)

@router.get("/api/campeonatos/{campeonato_id}")
def obter_campeonato(campeonato_id: int, session: Session = Depends(get_session)):
    return _obter_campeonato(session, campeonato_id)


# --- API PARTIDAS / CLASSIFICAÇÃO ---

@router.post("/api/campeonatos/{campeonato_id}/partidas/gerar")
def gerar_partidas(campeonato_id: int, session: Session = Depends(get_session)):
    """Sorteia o calendário da temporada regular (ou fase de grupos, dependendo do formato)."""
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
    return _atualizar_resultado(
        session,
        partida_id,
        resultado.gols_casa,
        resultado.gols_visitante,
        resultado.vencedor_penaltis,
    )

@router.get("/api/campeonatos/{campeonato_id}/classificacao")
def obter_classificacao(campeonato_id: int, session: Session = Depends(get_session)):
    return _calcular_classificacao(session, campeonato_id)


# --- API PLAYOFFS (mata-mata) ---

@router.post("/api/campeonatos/{campeonato_id}/playoffs/gerar")
def gerar_playoffs(campeonato_id: int, session: Session = Depends(get_session)):
    """Gera as Quartas de Final a partir dos 2 primeiros de cada grupo."""
    return _gerar_playoffs(session, campeonato_id)

@router.post("/api/campeonatos/{campeonato_id}/playoffs/avancar")
def avancar_fase_playoffs(campeonato_id: int, session: Session = Depends(get_session)):
    """Gera a próxima fase do mata-mata (Semifinal, Final) ou devolve o campeão."""
    return _avancar_fase_playoffs(session, campeonato_id)