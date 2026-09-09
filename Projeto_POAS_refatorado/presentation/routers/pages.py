from typing import Optional

from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from domain.entities.usuario import Usuario
from presentation.dependencies import obter_usuario_logado

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def read_root(request: Request, usuario: Optional[Usuario] = Depends(obter_usuario_logado)):
    return templates.TemplateResponse(
        request=request,
        name="base.html",
        context={"nome": usuario.nome if usuario else None},
    )


@router.get("/cadastro-page", response_class=HTMLResponse)
def cadastro_page(request: Request, usuario: Optional[Usuario] = Depends(obter_usuario_logado)):
    if usuario:
        return RedirectResponse(url="/home-page", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request=request, name="cadastro.html")


@router.get("/login-page", response_class=HTMLResponse)
def login_page(request: Request, usuario: Optional[Usuario] = Depends(obter_usuario_logado)):
    if usuario:
        return RedirectResponse(url="/home-page", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request=request, name="login.html")


@router.get("/videos-page", response_class=HTMLResponse)
def videos_page(request: Request, usuario: Optional[Usuario] = Depends(obter_usuario_logado)):
    return templates.TemplateResponse(
        request=request,
        name="videos.html",
        context={"nome": usuario.nome if usuario else None},
    )


@router.get("/times-page", response_class=HTMLResponse)
def times_page(request: Request, usuario: Optional[Usuario] = Depends(obter_usuario_logado)):
    return templates.TemplateResponse(
        request=request,
        name="times.html",
        context={"nome": usuario.nome if usuario else None},
    )


@router.get("/home-page", response_class=HTMLResponse)
def home_page(request: Request, usuario: Optional[Usuario] = Depends(obter_usuario_logado)):
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={"nome": usuario.nome if usuario else None},
    )


@router.get("/basquete-page", response_class=HTMLResponse)
def basquete_page(request: Request, usuario: Optional[Usuario] = Depends(obter_usuario_logado)):
    return templates.TemplateResponse(
        request=request,
        name="basquete.html",
        context={"nome": usuario.nome if usuario else None},
    )


@router.get("/ufc-page", response_class=HTMLResponse)
def ufc_page(request: Request, usuario: Optional[Usuario] = Depends(obter_usuario_logado)):
    return templates.TemplateResponse(
        request=request,
        name="ufc.html",
        context={"nome": usuario.nome if usuario else None},
    )


@router.get("/futebol-americano-page", response_class=HTMLResponse)
def futebol_americano_page(request: Request, usuario: Optional[Usuario] = Depends(obter_usuario_logado)):
    return templates.TemplateResponse(
        request=request,
        name="futebol_americano.html",
        context={"nome": usuario.nome if usuario else None},
    )


@router.get("/formula1-page", response_class=HTMLResponse)
def formula1_page(request: Request, usuario: Optional[Usuario] = Depends(obter_usuario_logado)):
    return templates.TemplateResponse(
        request=request,
        name="formula1.html",
        context={"nome": usuario.nome if usuario else None},
    )


@router.get("/usuario-page", response_class=HTMLResponse)
def usuario_page(request: Request, usuario: Optional[Usuario] = Depends(obter_usuario_logado)):
    if not usuario:
        return RedirectResponse(url="/login-page", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        request=request,
        name="area_usuario.html",
        context={"nome": usuario.nome},
    )
