from sqlmodel import SQLModel, create_engine, Session

from infrastructure.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    echo=True,
    connect_args={"check_same_thread": False},
)


def create_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
