from abc import ABC, abstractmethod
from typing import List, Optional

from domain.entities.campeonato import Campeonato


class CampeonatoRepository(ABC):
    """Contrato de persistência de campeonatos.

    A camada de aplicação depende desta abstração, nunca de uma
    implementação concreta de banco de dados (Dependency Inversion).
    """

    @abstractmethod
    def salvar(self, campeonato: Campeonato) -> Campeonato:
        ...

    @abstractmethod
    def listar_todos(self) -> List[Campeonato]:
        ...

    @abstractmethod
    def buscar_por_id(self, campeonato_id: int) -> Optional[Campeonato]:
        ...
