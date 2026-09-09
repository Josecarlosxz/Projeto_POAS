from typing import Optional

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from domain.entities.usuario import Usuario
from presentation.dependencies import obter_usuario_logado

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/simulador-page", response_class=HTMLResponse)
def simulador_page(request: Request, usuario: Optional[Usuario] = Depends(obter_usuario_logado)):
    return templates.TemplateResponse(
        request=request,
        name="simulador.html",
        context={"nome": usuario.nome if usuario else None},
    )


@router.get("/api/simulador/confrontos-iniciais")
def obter_confrontos_iniciais():
    quartas_de_final = [
        {"id_jogo": "q1", "time1": "NaVi", "time2": "FaZe"},
        {"id_jogo": "q2", "time1": "Vitality", "time2": "G2 Esports"},
        {"id_jogo": "q3", "time1": "FURIA", "time2": "MOUZ"},
        {"id_jogo": "q4", "time1": "Team Spirit", "time2": "Virtus.pro"},
    ]
    return {"quartas": quartas_de_final}
