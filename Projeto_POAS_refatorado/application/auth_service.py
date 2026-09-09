from typing import Optional

from sqlmodel import Session

from domain.entities.usuario import Usuario
from domain.schemas.usuario_schemas import TokenResponse
from infrastructure.repositories.usuario_repository_sql import UsuarioRepositorySQL
from infrastructure.security import hash_password, verify_password, create_access_token


def cadastrar_usuario(session: Session, nome: str, email: str, senha: str) -> Usuario:
    repo = UsuarioRepositorySQL(session)

    if repo.buscar_por_email(email):
        raise ValueError("Este email já está cadastrado!")

    novo_usuario = Usuario(nome=nome, email=email, senha_hash=hash_password(senha))
    return repo.salvar(novo_usuario)


def autenticar_usuario(session: Session, email: str, senha: str) -> Usuario:
    repo = UsuarioRepositorySQL(session)
    usuario = repo.buscar_por_email(email)

    if not usuario or not verify_password(senha, usuario.senha_hash):
        raise ValueError("Email ou senha incorretos")

    return usuario


def gerar_token_para(usuario: Usuario) -> TokenResponse:
    access_token = create_access_token(subject=usuario.email)
    return TokenResponse(access_token=access_token)


def obter_usuario_por_email(session: Session, email: str) -> Optional[Usuario]:
    return UsuarioRepositorySQL(session).buscar_por_email(email)
