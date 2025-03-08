import pytest
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import declarative_base
from starlette.testclient import TestClient

from backend import app
from backend.dependencies import Session, get_session

@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base = declarative_base()
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture
def client(session, monkeypatch):
    # override authentication functions
    # monkeypatch.setattr(auth, "hash_password", hash_password_stub)
    # monkeypatch.setattr(auth, "check_password", check_password_stub)
    
    # set up the client
    app.dependency_overrides[get_session] = lambda: session
    yield TestClient(app)
    app.dependency_overrides.clear()
    
@pytest.fixture
def exception():
    # function to generate an error message
    def _exception(error: str, message: str) -> dict:
        return { "error": error, "message": message }
    return _exception