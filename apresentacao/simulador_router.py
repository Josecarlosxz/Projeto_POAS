from typing import Optional

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from dados.models import Usuario
from negocio.auth_service import obter_usuario_logado
from negocio.simulador_service import obter_confrontos_iniciais as _obter_confrontos_iniciais

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# -- SIMULADOR DE CAMPEONATOS

@router.get("/simulador-page", response_class=HTMLResponse)
def simulador_page(request: Request, usuario: Optional[Usuario] = Depends(obter_usuario_logado)):
    return templates.TemplateResponse(
        request=request,
        name="simulador.html",
        context={
            "nome": usuario.nome if usuario else None
        }
    )

@router.get("/api/simulador/confrontos-iniciais")
def obter_confrontos_iniciais():
    return _obter_confrontos_iniciais()
