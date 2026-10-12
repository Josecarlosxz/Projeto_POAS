from typing import Optional

from fastapi import APIRouter, Depends, Form
from sqlmodel import Session

from acesso_dados.database import get_session
from dados.models import Usuario, ResultadoPartida, ResultadoLuta, LutaRequest, CardRequest
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
    atualizar_resultado_luta as _atualizar_resultado_luta,
    criar_luta as _criar_luta,
    remover_luta as _remover_luta,
    listar_cards as _listar_cards,
    criar_card as _criar_card,
    remover_card as _remover_card,
)

router = APIRouter()

# --- API CAMPEONATOS ---

@router.post("/api/campeonatos")
def criar_campeonato(
    nome: str = Form(...),
    esporte: str = Form(...),
    times: str = Form(...), 
    configuracao: Optional[str] = Form(None),
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


# --- API UFC (lutas por categoria + luta de título) ---

@router.put("/api/partidas/{partida_id}/resultado-luta")
def atualizar_resultado_luta(
    partida_id: int,
    resultado: ResultadoLuta,
    session: Session = Depends(get_session)
):
    """Registra o vencedor e o método (KO/TKO/SUB/DEC) de uma luta de UFC."""
    return _atualizar_resultado_luta(session, partida_id, resultado.vencedor, resultado.metodo)

@router.get("/api/campeonatos/{campeonato_id}/cards")
def listar_cards(campeonato_id: int, session: Session = Depends(get_session)):
    return _listar_cards(session, campeonato_id)

@router.post("/api/campeonatos/{campeonato_id}/cards")
def criar_card(campeonato_id: int, dados: CardRequest, session: Session = Depends(get_session)):
    """Cria um card (evento) de UFC com o nome escolhido pelo usuário."""
    return _criar_card(session, campeonato_id, dados.nome)

@router.delete("/api/cards/{card_id}")
def remover_card(card_id: int, session: Session = Depends(get_session)):
    """Remove um card (só se nenhuma luta dele tiver resultado)."""
    return _remover_card(session, card_id)

@router.post("/api/cards/{card_id}/lutas")
def criar_luta(card_id: int, dados: LutaRequest, session: Session = Depends(get_session)):
    """Adiciona uma luta ao card: categoria, os dois lutadores e se vale o cinturão."""
    return _criar_luta(
        session, card_id, dados.categoria, dados.lutador_casa, dados.lutador_visitante, dados.titulo
    )

@router.delete("/api/lutas/{partida_id}")
def remover_luta(partida_id: int, session: Session = Depends(get_session)):
    """Remove uma luta marcada por engano (só se ainda não tiver resultado)."""
    return _remover_luta(session, partida_id)