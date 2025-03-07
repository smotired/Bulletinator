"""Dependencies for application.

Args:
    engine (sqlalchemy.engine.Engine): The database engine
    DBSession (Session): A database session as a dependency
"""

from typing import Annotated

from fastapi import Depends

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.config import settings
from backend.database.schema import * # includes Base

engine = create_engine(settings.db_url, echo=True)
Session = sessionmaker(bind=engine)

def create_db_tables():
    """Ensure the database and tables are created."""

    Base.metadata.create_all(engine)

    if settings.db_sqlite:
        with engine.connect() as connection:
            connection.execute(text("PRAGMA foreign_key=ON"))

def get_session():
    """Database session dependency."""

    with Session() as session:
        yield session

DBSession = Annotated[Session, Depends(get_session)]
