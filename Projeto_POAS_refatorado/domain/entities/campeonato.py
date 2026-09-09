from typing import Optional
from datetime import datetime, timezone

from sqlmodel import SQLModel, Field


class Campeonato(SQLModel, table=True):
    """Entidade de domínio / tabela do banco de dados."""

    id: Optional[int] = Field(default=None, primary_key=True)

    nome: str
    esporte: str
    quantidade_times: int
    times: str  # lista de times serializada em JSON
    criador_id: Optional[int] = Field(default=None, foreign_key="usuarios.id")

    criado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
