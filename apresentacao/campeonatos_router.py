from typing import Optional

from fastapi import APIRouter, Depends, Form
from sqlmodel import Session

from acesso_dados.database import get_session
from dados.models import Usuario
from negocio.auth_service import obter_usuario_logado
from negocio.campeonato_service import (
    criar_campeonato as _criar_campeonato,
    listar_campeonatos as _listar_campeonatos,
    obter_campeonato as _obter_campeonato,
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
