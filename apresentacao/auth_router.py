from fastapi import APIRouter, Depends, status, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session

from acesso_dados.database import get_session
from dados.models import Usuario, TokenResponse
from negocio.auth_service import create_access_token, get_current_user
from negocio.cadastro_service import registrar_usuario, autenticar_usuario

router = APIRouter()

# --- ROTAS HTML de FORMULÁRIOS (mantidas, usando hash) ---

@router.post("/cadastro")
def cadastrar_usuario(
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    session: Session = Depends(get_session),
):
    novo_usuario = registrar_usuario(session, nome, email, senha)

    if novo_usuario is None:
        return HTMLResponse(
            content="<h3>Erro: Este email já está cadastrado!</h3><a href='/cadastro-page'>Tentar novamente</a>",
            status_code=400,
        )

    return RedirectResponse(url="/login-page", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/login")
def logar_usuario(
    email: str = Form(...),
    senha: str = Form(...),
    session: Session = Depends(get_session),
):
    usuario = autenticar_usuario(session, email, senha)

    if not usuario:
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

# --- ENDPOINTS API (JWT) ---

@router.post("/api/cadastro", response_class=HTMLResponse)
def api_cadastrar_usuario(
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    session: Session = Depends(get_session),
):
    novo_usuario = registrar_usuario(session, nome, email, senha)
    if novo_usuario is None:
        return HTMLResponse(content="<h3>Erro: Este email já está cadastrado!</h3>", status_code=400)

    return RedirectResponse(url="/api/login", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/api/login", response_model=TokenResponse)
def api_login(
    email: str = Form(...),
    senha: str = Form(...),
    session: Session = Depends(get_session),
):
    usuario = autenticar_usuario(session, email, senha)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha incorretos")

    access_token = create_access_token(subject=usuario.email)
    return TokenResponse(access_token=access_token)

@router.get("/api/me")
def api_me(current_user: Usuario = Depends(get_current_user)):
    return {"id": current_user.id, "nome": current_user.nome, "email": current_user.email, "criado_em": current_user.criado_em}
