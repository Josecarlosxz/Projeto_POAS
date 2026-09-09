from typing import Optional
from datetime import datetime, timezone

from sqlmodel import SQLModel, Field


class Usuario(SQLModel, table=True):
    """Entidade de domínio / tabela do banco de dados."""

    __tablename__ = "usuarios"

    id: Optional[int] = Field(default=None, primary_key=True)

    nome: str
    email: str = Field(unique=True, index=True)
    senha_hash: str

    criado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
