from fastapi import FastAPI, Depends, status, Form, Request, Cookie, HTTPException , WebSocket
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse , JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select
from typing import Optional

from contextlib import asynccontextmanager
import traceback

import bcrypt
from jose import jwt, JWTError
from datetime import datetime, timezone, timedelta

from fastapi.security import OAuth2PasswordBearer

from database import *
from models import *

# --- JWT config ---
SECRET_KEY = "change_me_super_secret"  
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db()
    yield

app = FastAPI(lifespan=lifespan)

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.exception_handler(Exception)
async def validation_exception_handler(request: Request, exc: Exception):
    return PlainTextResponse(str(traceback.format_exc()), status_code=500)

# --- SISTEMA DE VERIFICAÇÃO DE SESSÃO (cookie) ---

def obter_usuario_logado(
    session: Session = Depends(get_session),
    usuario_email: Optional[str] = Cookie(None)
) -> Optional[Usuario]:
    if not usuario_email:
        return None
    statement = select(Usuario).where(Usuario.email == usuario_email)
    return session.exec(statement).first()

# --- JWT helpers ---

def create_access_token(*, subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain_password: str, password_hash: str) -> bool:
    password_bytes = plain_password.encode('utf-8')
    hash_bytes = password_hash.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hash_bytes)

def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> Usuario:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("sub")
        if not email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    statement = select(Usuario).where(Usuario.email == email)
    usuario = session.exec(statement).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado")
    return usuario

def protected_me(current_user: Usuario = Depends(get_current_user)):
    return {"id": current_user.id, "nome": current_user.nome, "email": current_user.email} 

# --- ROTAS PARA RENDERIZAR PÁGINAS ---

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, usuario: Optional[Usuario] = Depends(obter_usuario_logado)):
    nome_usuario = usuario.nome if usuario else None
    return templates.TemplateResponse(
        request=request,
        name="base.html",
        context={"nome": nome_usuario},
    )

@app.get("/cadastro-page", response_class=HTMLResponse)
def cadastro_page(request: Request, usuario: Optional[Usuario] = Depends(obter_usuario_logado)):
    if usuario:
        return RedirectResponse(url="/home-page", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request=request, name="cadastro.html")

@app.get("/login-page", response_class=HTMLResponse)
def login_page(request: Request, usuario: Optional[Usuario] = Depends(obter_usuario_logado)):
    if usuario:
        return RedirectResponse(url="/home-page", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request=request, name="login.html")

@app.get("/home-page", response_class=HTMLResponse)
def home_page(request: Request, usuario: Optional[Usuario] = Depends(obter_usuario_logado)):
    if not usuario:
        return RedirectResponse(url="/login-page", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={"nome": usuario.nome},
    )

@app.get("/basquete-page", response_class=HTMLResponse)
def basquete_page(
    request: Request,
    usuario: Optional[Usuario] = Depends(obter_usuario_logado)
):

    return templates.TemplateResponse(
        request=request,
        name="basquete.html",
        context={
            "nome": usuario.nome if usuario else None
        }
    )

@app.get("/ufc-page", response_class=HTMLResponse)
def ufc_page(
    request: Request,
    usuario: Optional[Usuario] = Depends(obter_usuario_logado)
):

    return templates.TemplateResponse(
        request=request,
        name="ufc.html",
        context={
            "nome": usuario.nome if usuario else None
        }
    )

@app.get("/futebol-americano-page", response_class=HTMLResponse)
def futebol_americano_page(
    request: Request,
    usuario: Optional[Usuario] = Depends(obter_usuario_logado)
):

    return templates.TemplateResponse(
        request=request,
        name="futebol_americano.html",
        context={
            "nome": usuario.nome if usuario else None
        }
    )

@app.get("/formula1-page", response_class=HTMLResponse)
def formula1_page(
    request: Request,
    usuario: Optional[Usuario] = Depends(obter_usuario_logado)
):

    return templates.TemplateResponse(
        request=request,
        name="formula1.html",
        context={
            "nome": usuario.nome if usuario else None
        }
    )

@app.get("/usuario-page", response_class=HTMLResponse)
def usuario_page(request: Request, usuario: Optional[Usuario] = Depends(obter_usuario_logado)):
    if not usuario:
        return RedirectResponse(url="/login-page", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request=request,
        name="area_usuario.html",
        context={"nome": usuario.nome},
    )

# --- ROTAS HTML de FORMULÁRIOS (mantidas, usando hash) ---

@app.post("/cadastro")
def cadastrar_usuario(
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    session: Session = Depends(get_session),
):
    statement = select(Usuario).where(Usuario.email == email)
    usuario_existente = session.exec(statement).first()

    if usuario_existente:
        return HTMLResponse(
            content="<h3>Erro: Este email já está cadastrado!</h3><a href='/cadastro-page'>Tentar novamente</a>",
            status_code=400,
        )

    senha_bytes = senha.encode('utf-8')
    senha_hash = bcrypt.hashpw(senha_bytes, bcrypt.gensalt()).decode('utf-8')
    novo_usuario = Usuario(nome=nome, email=email, senha_hash=senha_hash)
    session.add(novo_usuario)
    session.commit()
    session.refresh(novo_usuario)

    return RedirectResponse(url="/login-page", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/login")
def logar_usuario(
    request: Request,
    email: str = Form(...),
    senha: str = Form(...),
    session: Session = Depends(get_session),
):
    statement = select(Usuario).where(Usuario.email == email)
    usuario = session.exec(statement).first()

    if not usuario or not verify_password(senha, usuario.senha_hash):
        return HTMLResponse(
            content="<h3>Erro: Email ou senha incorretos!</h3><a href='/login-page'>Tentar novamente</a>",
            status_code=401,
        )

    response = RedirectResponse(url="/home-page", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="usuario_email", value=usuario.email, httponly=True, max_age=3600)
    return response

@app.get("/logout")
def deslogar_usuario():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="usuario_email")
    return response

# --- ENDPOINTS API (JWT) ---

@app.post("/api/cadastro", response_class=HTMLResponse)
def api_cadastrar_usuario(
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    session: Session = Depends(get_session),
):
    statement = select(Usuario).where(Usuario.email == email)
    usuario_existente = session.exec(statement).first()
    if usuario_existente:
        return HTMLResponse(content="<h3>Erro: Este email já está cadastrado!</h3>", status_code=400)
    
    senha_bytes = senha.encode('utf-8')
    senha_hash = bcrypt.hashpw(senha_bytes, bcrypt.gensalt()).decode('utf-8')
    novo_usuario = Usuario(nome=nome, email=email, senha_hash=senha_hash)
    session.add(novo_usuario)
    session.commit()
    session.refresh(novo_usuario)
    return RedirectResponse(url="/api/login", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/api/login", response_model=TokenResponse)
def api_login(
    email: str = Form(...),
    senha: str = Form(...),
    session: Session = Depends(get_session),
):
    statement = select(Usuario).where(Usuario.email == email)
    usuario = session.exec(statement).first()
    if not usuario or not verify_password(senha, usuario.senha_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha incorretos")

    access_token = create_access_token(subject=usuario.email)
    return TokenResponse(access_token=access_token)

@app.get("/api/me")
def api_me(current_user: Usuario = Depends(get_current_user)):
    return {"id": current_user.id, "nome": current_user.nome, "email": current_user.email, "criado_em": current_user.criado_em}

# --- API NOTÍCIAS ---

import requests
API_KEY = "d5c981928b0548918cd5f360ffb63759"

noticias_cache = []
ultimo_update = None

@app.get("/api/noticias")
def obter_noticias():

    url = (
        "https://newsapi.org/v2/everything?"
        "q=futebol OR soccer OR football"
        "&language=pt"
        "&sortBy=publishedAt"
        f"&apiKey={API_KEY}"
    )

    resposta = requests.get(url)

    if resposta.status_code != 200:
        return JSONResponse(
            status_code=500,
            content={"erro": "Falha ao buscar notícias"}
        )

    dados = resposta.json()

    noticias = []

    for artigo in dados["articles"][:20]:

        if artigo["title"] is None or artigo["urlToImage"] is None:
            continue

        noticias.append({
            "titulo": artigo["title"],
            "descricao": artigo["description"],
            "imagem": artigo["urlToImage"],
            "link": artigo["url"],
            "fonte": artigo["source"]["name"],
            "data": artigo["publishedAt"]
        })

    return noticias

@app.get("/api/basquete")
def basquete():

    url = (
        "https://newsapi.org/v2/everything?"
        'q=("NBA" OR "basketball")'
        "&language=pt"
        "&sortBy=publishedAt"
        f"&apiKey={API_KEY}"
    )

    resposta = requests.get(url)

    artigos = resposta.json()["articles"]

    noticias = []

    palavras = [
        "nba",
        "basketball",
        "lebron",
        "stephen curry",
        "warriors",
        "lakers",
        "celtics",
        "bucks",
        "knicks"
    ]

    for artigo in artigos:

        if artigo["title"] is None or artigo["urlToImage"] is None:
            continue

        texto = (
            (artigo["title"] or "") +
            " " +
            (artigo["description"] or "")
        ).lower()

        if any(palavra in texto for palavra in palavras):
            noticias.append(artigo)

    return noticias

@app.get("/api/ufc")
def ufc():

    url = (
        "https://newsapi.org/v2/everything?"
        'q=("UFC" OR "MMA")'
        "&language=pt"
        "&sortBy=publishedAt"
        f"&apiKey={API_KEY}"
    )

    resposta = requests.get(url)

    artigos = resposta.json()["articles"]

    noticias = []

    for artigo in artigos:

        if artigo["title"] is None or artigo["urlToImage"] is None:
            continue

        titulo = artigo["title"].lower()

        if (
            "ufc" in titulo
            or "mma" in titulo
        ):
            noticias.append(artigo)

    return noticias

@app.get("/api/futebol-americano")
def futebol_americano():

    url = (
        "https://newsapi.org/v2/everything?"
        'q=("NFL" OR "American Football")'
        "&language=pt"
        "&sortBy=publishedAt"
        f"&apiKey={API_KEY}"
    )

    resposta = requests.get(url)

    artigos = resposta.json()["articles"]

    noticias = []

    palavras = [
        "nfl",
        "american football",
        "chiefs",
        "eagles",
        "cowboys",
        "packers",
        "49ers",
        "ravens",
        "patrick mahomes",
        "josh allen"
    ]

    for artigo in artigos:
        
        if artigo["title"] is None or artigo["urlToImage"] is None:
            continue

        texto = (
            (artigo["title"] or "") +
            " " +
            (artigo["description"] or "")
        ).lower()

        if any(palavra in texto for palavra in palavras):

            noticias.append({
                "title": artigo["title"],
                "description": artigo["description"],
                "url": artigo["url"],
                "urlToImage": artigo["urlToImage"],
                "source": artigo["source"]
            })

    return noticias

@app.get("/api/formula1")
def formula1():

    url = (
        "https://newsapi.org/v2/everything?"
        'q=("Formula 1" OR "F1")'
        '&language=pt'
        "&sortBy=publishedAt"
        f"&apiKey={API_KEY}"
    )

    resposta = requests.get(url)

    artigos = resposta.json()["articles"]

    noticias = []

    palavras = [
        "formula 1",
        "f1",
        "verstappen",
        "hamilton",
        "ferrari",
        "red bull",
        "mercedes",
        "mclaren",
        "leclerc",
        "norris",
        "russell",
        "aston martin"
    ]

    for artigo in artigos:

        texto = (
            (artigo["title"] or "") +
            " " +
            (artigo["description"] or "")
        ).lower()

        if any(palavra in texto for palavra in palavras):

            if not all([
                artigo.get("title"),
                artigo.get("description"),
                artigo.get("url"),
                artigo.get("urlToImage")
            ]):
                continue

            noticias.append({
                "title": artigo["title"],
                "description": artigo["description"],
                "url": artigo["url"],
                "urlToImage": artigo["urlToImage"],
                "source": artigo["source"]
            })

    return noticias