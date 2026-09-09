from typing import Optional

from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from application import campeonatos_service
from domain.entities.usuario import Usuario
from infrastructure.database import get_session
from presentation.dependencies import obter_usuario_logado

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# --- Páginas ---

@router.get("/campeonatos-page", response_class=HTMLResponse)
def campeonatos_page(request: Request, usuario: Optional[Usuario] = Depends(obter_usuario_logado)):
    return templates.TemplateResponse(
        request=request,
        name="campeonatos.html",
        context={"nome": usuario.nome if usuario else None},
    )


@router.get("/campeonato-page/{campeonato_id}", response_class=HTMLResponse)
def campeonato_detalhe_page(
    campeonato_id: int,
    request: Request,
    usuario: Optional[Usuario] = Depends(obter_usuario_logado),
):
    return templates.TemplateResponse(
        request=request,
        name="campeonato_detalhe.html",
        context={
            "nome": usuario.nome if usuario else None,
            "campeonato_id": campeonato_id,
        },
    )


# --- API ---

@router.post("/api/campeonatos")
def criar_campeonato(
    nome: str = Form(...),
    esporte: str = Form(...),
    times: str = Form(...),  # JSON string, ex: '["Time A","Time B"]'
    session: Session = Depends(get_session),
    usuario: Optional[Usuario] = Depends(obter_usuario_logado),
):
    try:
        return campeonatos_service.criar_campeonato(
            session,
            nome=nome,
            esporte=esporte,
            times_json=times,
            criador_id=usuario.id if usuario else None,
        )
    except ValueError as erro:
        raise HTTPException(status_code=400, detail=str(erro))


@router.get("/api/campeonatos")
def listar_campeonatos(session: Session = Depends(get_session)):
    return campeonatos_service.listar_campeonatos(session)


@router.get("/api/campeonatos/{campeonato_id}")
def obter_campeonato(campeonato_id: int, session: Session = Depends(get_session)):
    try:
        return campeonatos_service.obter_campeonato(session, campeonato_id)
    except LookupError as erro:
        raise HTTPException(status_code=404, detail=str(erro))
