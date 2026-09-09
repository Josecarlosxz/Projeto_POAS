from typing import Optional

from sqlmodel import Session, select

from domain.entities.usuario import Usuario
from domain.repositories.usuario_repository import UsuarioRepository


class UsuarioRepositorySQL(UsuarioRepository):
    """Implementação concreta do repositório de usuários usando SQLModel/SQLite."""

    def __init__(self, session: Session):
        self.session = session

    def buscar_por_email(self, email: str) -> Optional[Usuario]:
        statement = select(Usuario).where(Usuario.email == email)
        return self.session.exec(statement).first()

    def salvar(self, usuario: Usuario) -> Usuario:
        self.session.add(usuario)
        self.session.commit()
        self.session.refresh(usuario)
        return usuario
