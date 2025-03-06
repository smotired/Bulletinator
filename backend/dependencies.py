"""Dependencies for application.

Args:
    engine (sqlalchemy.engine.Engine): The database engine
    DBSession (Session): A database session as a dependency
"""

from typing import Annotated

from fastapi import Depends
from fastapi.security import APIKeyCookie, HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, SQLModel, create_engine, text
from backend.config import settings

engine = create_engine(settings.db_url, echo=True)

def create_db_tables():
    """Ensure the database and tables are created."""

    SQLModel.metadata.create_all(engine)

    if settings.db_sqlite:
        with engine.connect() as connection:
            connection.execute(text("PRAGMA foreign_key=ON"))

def get_session():
    """Database session dependency."""

    with Session(engine) as session:
        yield session

DBSession = Annotated[Session, Depends(get_session)]
