from typing import List, Optional

from sqlmodel import Session, select

from domain.entities.campeonato import Campeonato
from domain.repositories.campeonato_repository import CampeonatoRepository


class CampeonatoRepositorySQL(CampeonatoRepository):
    """Implementação concreta do repositório de campeonatos usando SQLModel/SQLite."""

    def __init__(self, session: Session):
        self.session = session

    def salvar(self, campeonato: Campeonato) -> Campeonato:
        self.session.add(campeonato)
        self.session.commit()
        self.session.refresh(campeonato)
        return campeonato

    def listar_todos(self) -> List[Campeonato]:
        statement = select(Campeonato).order_by(Campeonato.id.desc())
        return list(self.session.exec(statement).all())

    def buscar_por_id(self, campeonato_id: int) -> Optional[Campeonato]:
        return self.session.get(Campeonato, campeonato_id)
