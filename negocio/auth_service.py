from typing import Optional

import bcrypt
from fastapi import Depends, status, Cookie, HTTPException
from jose import jwt, JWTError
from sqlmodel import Session
from datetime import datetime, timezone, timedelta

from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, oauth2_scheme
from acesso_dados.database import get_session
from acesso_dados.usuario_repository import buscar_usuario_por_email
from dados.models import Usuario


# --- SISTEMA DE VERIFICAÇÃO DE SESSÃO (cookie) ---

def obter_usuario_logado(
    session: Session = Depends(get_session),
    usuario_email: Optional[str] = Cookie(None)
) -> Optional[Usuario]:
    if not usuario_email:
        return None
    return buscar_usuario_por_email(session, usuario_email)


# --- JWT helpers ---

def create_access_token(*, subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain_password: str, password_hash: str) -> bool:
    password_bytes = plain_password.encode('utf-8')
    hash_bytes = password_hash.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hash_bytes)

def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> Usuario:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("sub")
        if not email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    usuario = buscar_usuario_por_email(session, email)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado")
    return usuario

def protected_me(current_user: Usuario = Depends(get_current_user)):
    return {"id": current_user.id, "nome": current_user.nome, "email": current_user.email}
