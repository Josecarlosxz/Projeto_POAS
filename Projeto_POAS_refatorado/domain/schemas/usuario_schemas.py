from pydantic import BaseModel, EmailStr


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
