from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime , timezone
from pydantic import BaseModel, EmailStr

# Classes

class Usuario(SQLModel, table=True):
    __tablename__ = "usuarios"

    id: Optional[int] = Field(default=None, primary_key=True)

    nome: str
    email: str = Field(unique=True, index=True)
    senha: str

    criado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Schemas

class UsuarioCadastro(BaseModel):
    nome: str
    email: EmailStr
    senha: str


class UsuarioLogin(BaseModel):
    email: EmailStr
    senha: str