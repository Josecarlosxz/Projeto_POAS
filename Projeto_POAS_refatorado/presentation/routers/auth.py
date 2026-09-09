from fastapi import APIRouter, Form, Depends, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session

from application import auth_service
from domain.entities.usuario import Usuario
from domain.schemas.usuario_schemas import TokenResponse
from infrastructure.database import get_session
from presentation.dependencies import get_current_user

router = APIRouter()


# --- Rotas HTML de formulário (sessão via cookie) ---

@router.post("/cadastro")
def cadastrar_usuario(
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    session: Session = Depends(get_session),
):
    try:
        auth_service.cadastrar_usuario(session, nome, email, senha)
    except ValueError as erro:
        return HTMLResponse(
            content=f"<h3>Erro: {erro}</h3><a href='/cadastro-page'>Tentar novamente</a>",
            status_code=400,
        )
    return RedirectResponse(url="/login-page", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/login")
def logar_usuario(
    email: str = Form(...),
    senha: str = Form(...),
    session: Session = Depends(get_session),
):
    try:
        usuario = auth_service.autenticar_usuario(session, email, senha)
    except ValueError:
        return HTMLResponse(
            content="<h3>Erro: Email ou senha incorretos!</h3><a href='/login-page'>Tentar novamente</a>",
            status_code=401,
        )

    response = RedirectResponse(url="/home-page", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="usuario_email", value=usuario.email, httponly=True, max_age=3600)
    return response


@router.get("/logout")
def deslogar_usuario():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="usuario_email")
    return response


# --- Endpoints API (sessão via JWT) ---

@router.post("/api/cadastro", response_class=HTMLResponse)
def api_cadastrar_usuario(
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    session: Session = Depends(get_session),
):
    try:
        auth_service.cadastrar_usuario(session, nome, email, senha)
    except ValueError as erro:
        return HTMLResponse(content=f"<h3>Erro: {erro}</h3>", status_code=400)
    return RedirectResponse(url="/api/login", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/api/login", response_model=TokenResponse)
def api_login(
    email: str = Form(...),
    senha: str = Form(...),
    session: Session = Depends(get_session),
):
    try:
        usuario = auth_service.autenticar_usuario(session, email, senha)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha incorretos")
    return auth_service.gerar_token_para(usuario)


@router.get("/api/me")
def api_me(current_user: Usuario = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "nome": current_user.nome,
        "email": current_user.email,
        "criado_em": current_user.criado_em,
    }
