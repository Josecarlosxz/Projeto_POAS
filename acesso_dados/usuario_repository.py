from typing import Optional
from sqlmodel import Session, select

from dados.models import Usuario


def buscar_usuario_por_email(session: Session, email: str) -> Optional[Usuario]:
    statement = select(Usuario).where(Usuario.email == email)
    return session.exec(statement).first()


def salvar_usuario(session: Session, usuario: Usuario) -> Usuario:
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario
