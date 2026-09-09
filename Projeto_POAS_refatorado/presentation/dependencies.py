from typing import Optional

from fastapi import Depends, Cookie, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from application.auth_service import obter_usuario_por_email
from domain.entities.usuario import Usuario
from infrastructure.database import get_session
from infrastructure.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")


def obter_usuario_logado(
    session: Session = Depends(get_session),
    usuario_email: Optional[str] = Cookie(None),
) -> Optional[Usuario]:
    """Autenticação via cookie, usada nas páginas HTML."""
    if not usuario_email:
        return None
    return obter_usuario_por_email(session, usuario_email)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> Usuario:
    """Autenticação via JWT, usada nos endpoints /api/*."""
    payload = decode_access_token(token)
    email = payload.get("sub") if payload else None
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    usuario = obter_usuario_por_email(session, email)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado")
    return usuario
