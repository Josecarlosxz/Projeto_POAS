from typing import Optional

import bcrypt
from sqlmodel import Session

from acesso_dados.usuario_repository import buscar_usuario_por_email, salvar_usuario
from dados.models import Usuario
from negocio.auth_service import verify_password


def registrar_usuario(session: Session, nome: str, email: str, senha: str) -> Optional[Usuario]:
    usuario_existente = buscar_usuario_por_email(session, email)

    if usuario_existente:
        return None

    senha_bytes = senha.encode('utf-8')
    senha_hash = bcrypt.hashpw(senha_bytes, bcrypt.gensalt()).decode('utf-8')
    novo_usuario = Usuario(nome=nome, email=email, senha_hash=senha_hash)
    return salvar_usuario(session, novo_usuario)


def autenticar_usuario(session: Session, email: str, senha: str) -> Optional[Usuario]:
    usuario = buscar_usuario_por_email(session, email)

    if not usuario or not verify_password(senha, usuario.senha_hash):
        return None

    return usuario
