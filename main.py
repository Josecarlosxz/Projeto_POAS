from fastapi import FastAPI, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select
from database import create_db, get_session
from models import Usuario

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db()

# Rotas para renderizar pa

@app.get("/", response_class=HTMLResponse)
def read_root():
    with open("base.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/cadastro-page", response_class=HTMLResponse)
def cadastro_page():
    with open("cadastro.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/login-page", response_class=HTMLResponse)
def login_page():
    with open("login.html", "r", encoding="utf-8") as f:
        return f.read()


# -----------------------------------------------------------------------------
# ROTAS DE LÓGICA (Processamento dos Formulários)
# -----------------------------------------------------------------------------

@app.post("/cadastro")
def cadastrar_usuario(
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    session: Session = Depends(get_session)
):
    # Verificar se o email já está cadastrado
    statement = select(Usuario).where(Usuario.email == email)
    usuario_existente = session.exec(statement).first()
    
    if usuario_existente:
        return HTMLResponse(content="<h3>Erro: Este email já está cadastrado!</h3><a href='/cadastro-page'>Tentar novamente</a>", status_code=400)

    # Nota de segurança: Em produção, lembre-se de usar uma biblioteca como o bcrypt para hash de senha!
    novo_usuario = Usuario(nome=nome, email=email, senha=senha)
    
    session.add(novo_usuario)
    session.commit()
    session.refresh(novo_usuario)
    
    # Redireciona para a página de login após o cadastro com sucesso
    return RedirectResponse(url="/login-page", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/login")
def logar_usuario(
    email: str = Form(...),
    senha: str = Form(...),
    session: Session = Depends(get_session)
):
    # Buscar usuário pelo email
    statement = select(Usuario).where(Usuario.email == email)
    usuario = session.exec(statement).first()
    
    # Verificar se usuário existe e se a senha está correta
    if not usuario or usuario.senha != senha:
        return HTMLResponse(
            content="<h3>Erro: Email ou senha incorretos!</h3><a href='/login-page'>Tentar novamente</a>", 
            status_code=401
        )
    
    # 1. Abre o arquivo home.html recém-criado
    with open("home.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # 2. Substitui dinamicamente o marcador {nome} pelo nome real do usuário vindo do banco
    html_customizado = html_content.replace("{nome}", usuario.nome)
    
    # 3. Retorna a página customizada para o navegador
    return HTMLResponse(content=html_customizado, status_code=200)