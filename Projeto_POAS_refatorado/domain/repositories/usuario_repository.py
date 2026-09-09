from abc import ABC, abstractmethod
from typing import Optional

from domain.entities.usuario import Usuario


class UsuarioRepository(ABC):
    """Contrato de persistência de usuários.

    A camada de domínio/aplicação depende desta abstração, nunca de uma
    implementação concreta de banco de dados (Dependency Inversion).
    """

    @abstractmethod
    def buscar_por_email(self, email: str) -> Optional[Usuario]:
        ...

    @abstractmethod
    def salvar(self, usuario: Usuario) -> Usuario:
        ...
