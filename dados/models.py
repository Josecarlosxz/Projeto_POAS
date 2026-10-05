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

    # JSON (texto) com as opções específicas do esporte escolhidas na criação.
    # Ex.: futebol -> {"formato": "grupos_playoffs"}
    #      basquete -> {"conferencias": 2}
    #      ufc -> {"categorias": ["Peso Pena", "Peso Leve"], "lutadores_por_categoria": {...}}
    configuracao: Optional[str] = Field(default=None)


class Partida(SQLModel, table=True):
    __tablename__ = "partidas"

    id: Optional[int] = Field(default=None, primary_key=True)
    campeonato_id: int = Field(foreign_key="campeonato.id", index=True)

    rodada: int
    turno: int

    time_casa: str
    time_visitante: str

    gols_casa: Optional[int] = Field(default=None)
    gols_visitante: Optional[int] = Field(default=None)
    finalizada: bool = Field(default=False)

    # --- Campos genéricos usados por formatos de fase eliminatória / grupos / conferências ---
    # fase: None (temporada regular / pontos corridos) | "grupos" | "playoffs" | "wildcard" |
    #       "divisional" | "conferencia" | "final" | "titulo"
    fase: Optional[str] = Field(default=None)

    # grupo: nome do grupo na fase de grupos (futebol) - ex: "A", "B", "C", "D"
    grupo: Optional[str] = Field(default=None)

    # conferencia / divisao: usados por basquete (conferência) e NFL (conferência + divisão)
    conferencia: Optional[str] = Field(default=None)
    divisao: Optional[str] = Field(default=None)

    # etapa: rótulo legível da fase eliminatória, usado em qualquer esporte com mata-mata
    # ex.: "Quartas de Final", "Semifinal", "Final", "Wild Card", "Divisional",
    #      "Final de Conferência", "Super Bowl", "Luta pelo Cinturão"
    etapa: Optional[str] = Field(default=None)

    # categoria: usado pelo UFC (nome da categoria de peso)
    categoria: Optional[str] = Field(default=None)

    # método de vitória do UFC: "KO", "TKO", "SUB" ou "DEC". Preenchido só quando finalizada=True.
    metodo_vitoria: Optional[str] = Field(default=None)

    # vencedor_penaltis: usado em partidas de mata-mata (futebol) empatadas no tempo normal
    vencedor_penaltis: Optional[str] = Field(default=None)

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


class ResultadoPartida(BaseModel):
    gols_casa: int
    gols_visitante: int
    vencedor_penaltis: Optional[str] = None