from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime

# Classes

class Usuario(SQLModel, table=True):
    __tablename__ = "usuarios"

    id: Optional[int] = Field(default=None, primary_key=True)

    nome: str
    email: str = Field(unique=True, index=True)
    senha: str

    criado_em: datetime = Field(default_factory=datetime.utcnow)

# Schemas

from pydantic import BaseModel, EmailStr


class UsuarioCadastro(BaseModel):
    nome: str
    email: EmailStr
    senha: str


class UsuarioLogin(BaseModel):
    email: EmailStr
    senha: str