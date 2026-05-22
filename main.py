from fastapi import FastAPI, Depends, status, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse , PlainTextResponse
from fastapi.templating import Jinja2Templates  
from sqlmodel import Session, select

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

# Rotas para renderizar páginas

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="base.html")

@app.get("/cadastro-page", response_class=HTMLResponse)
def cadastro_page(request: Request):
    return templates.TemplateResponse(request=request, name="cadastro.html")

@app.get("/login-page", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

# Rotas de formulários

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
    
    return templates.TemplateResponse(
        "home.html", 
        {"request": request, "nome": usuario.nome}
    )