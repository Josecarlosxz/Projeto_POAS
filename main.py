from fastapi import FastAPI, Depends, status, Form, Request, Cookie, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select
from typing import Optional

from contextlib import asynccontextmanager
import traceback

from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timezone, timedelta


from fastapi.security import OAuth2PasswordBearer

from database import *
from models import *

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT config
SECRET_KEY = "change_me_super_secret"  # troque em produção
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
    return pwd_context.verify(plain_password, password_hash)

# --- Dependência para rotas protegidas (Bearer) ---

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

@app.get("/protected/me")
def protected_me(current_user: Usuario = Depends(get_current_user)):
    return {"id": current_user.id, "nome": current_user.nome, "email": current_user.email} 


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

    senha_hash = pwd_context.hash(senha)
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

    senha_hash = pwd_context.hash(senha)
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

