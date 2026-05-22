from fastapi import FastAPI, Depends, status, Form, Request, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates  
from sqlmodel import Session, select
from typing import Optional

from contextlib import asynccontextmanager
import traceback

from database import *
from models import *

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db()
    yield

app = FastAPI(lifespan=lifespan)

@app.exception_handler(Exception)
async def validation_exception_handler(request: Request, exc: Exception):
    return PlainTextResponse(str(traceback.format_exc()), status_code=500)

templates = Jinja2Templates(directory="templates")


# --- SISTEMA DE VERIFICAÇÃO DE SESSÃO ---
# Esta função verifica se o usuário tem o cookie de sessão ativo. 
# Se tiver, ela busca o usuário no banco de dados e o valida.
def obter_usuario_logado(
    session: Session = Depends(get_session), 
    usuario_email: Optional[str] = Cookie(None)
) -> Optional[Usuario]:
    if not usuario_email:
        return None
    statement = select(Usuario).where(Usuario.email == usuario_email)
    return session.exec(statement).first()


# --- ROTAS PARA RENDERIZAR PÁGINAS ---

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, usuario: Optional[Usuario] = Depends(obter_usuario_logado)):
    # Se o usuário estiver logado, passamos o nome dele para a base.html atualizar a navbar
    nome_usuario = usuario.nome if usuario else None
    return templates.TemplateResponse(
        request=request, 
        name="base.html", 
        context={"nome": nome_usuario}
    )

@app.get("/cadastro-page", response_class=HTMLResponse)
def cadastro_page(request: Request, usuario: Optional[Usuario] = Depends(obter_usuario_logado)):
    if usuario:
        return RedirectResponse(url="/home-page", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request=request, name="cadastro.html")

@app.get("/login-page", response_class=HTMLResponse)
def login_page(request: Request, usuario: Optional[Usuario] = Depends(obter_usuario_logado)):
    # Se o usuário já estiver logado e tentar acessar a tela de login, manda direto para a home
    if usuario:
        return RedirectResponse(url="/home-page", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request=request, name="login.html")

@app.get("/home-page", response_class=HTMLResponse)
def home_page(request: Request, usuario: Optional[Usuario] = Depends(obter_usuario_logado)):
    # Protege a rota: se não estiver logado, joga para a tela de login
    if not usuario:
        return RedirectResponse(url="/login-page", status_code=status.HTTP_303_SEE_OTHER)
    
    return templates.TemplateResponse(
        request=request, 
        name="home.html", 
        context={"nome": usuario.nome}
    )


# --- ROTAS DE FORMULÁRIOS ---

@app.post("/cadastro")
def cadastrar_usuario(
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    session: Session = Depends(get_session)
):
    statement = select(Usuario).where(Usuario.email == email)
    usuario_existente = session.exec(statement).first()
    
    if usuario_existente:
        return HTMLResponse(
            content="<h3>Erro: Este email já está cadastrado!</h3><a href='/cadastro-page'>Tentar novamente</a>", 
            status_code=400
        )

    novo_usuario = Usuario(nome=nome, email=email, senha=senha)
    session.add(novo_usuario)
    session.commit()
    session.refresh(novo_usuario)
    
    return RedirectResponse(url="/login-page", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/login")
def logar_usuario(
    request: Request, 
    email: str = Form(...),
    senha: str = Form(...),
    session: Session = Depends(get_session)
):
    statement = select(Usuario).where(Usuario.email == email)
    usuario = session.exec(statement).first()
    
    if not usuario or usuario.senha != senha:
        return HTMLResponse(
            content="<h3>Erro: Email ou senha incorretos!</h3><a href='/login-page'>Tentar novamente</a>", 
            status_code=401
        )
    
    # Criamos a resposta redirecionando o usuário para a página home estável do painel
    response = RedirectResponse(url="/home-page", status_code=status.HTTP_303_SEE_OTHER)
    
    # Injetamos o Cookie de Sessão no navegador. httponly=True evita ataques XSS maliciosos.
    response.set_cookie(key="usuario_email", value=usuario.email, httponly=True, max_age=3600) 
    return response


@app.get("/logout")
def deslogar_usuario():
    # Remove o cookie do navegador redirecionando o usuário de volta à raiz
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="usuario_email")
    return response