from typing import Optional
from sqlmodel import Session, select

from dados.models import Campeonato


def salvar_campeonato(session: Session, campeonato: Campeonato) -> Campeonato:
    session.add(campeonato)
    session.commit()
    session.refresh(campeonato)
    return campeonato


def listar_campeonatos(session: Session) -> list[Campeonato]:
    statement = select(Campeonato).order_by(Campeonato.id.desc())
    return session.exec(statement).all()


def obter_campeonato_por_id(session: Session, campeonato_id: int) -> Optional[Campeonato]:
    return session.get(Campeonato, campeonato_id)
