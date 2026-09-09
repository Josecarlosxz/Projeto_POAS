from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from pydantic import BaseModel, EmailStr

# Classes

class Usuario(SQLModel, table=True):
    __tablename__ = "usuarios"

    id: Optional[int] = Field(default=None, primary_key=True)

    nome: str
    email: str = Field(unique=True, index=True)
    senha_hash: str

    criado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Campeonato(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nome: str
    esporte: str
    quantidade_times: int
    times: str
    criador_id: Optional[int] = Field(default=None, foreign_key="usuarios.id")
    criado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Schemas

class UsuarioCadastro(BaseModel):
    nome: str
    email: EmailStr
    senha: str


class UsuarioLogin(BaseModel):
    email: EmailStr
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

