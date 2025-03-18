import pytest
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import declarative_base, sessionmaker
from starlette.testclient import TestClient

from backend import app
from backend.dependencies import get_session
from backend.database.schema import *

@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine) # uses the schema's Base
    Session = sessionmaker(bind=engine)
    with Session() as session:
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

# Initial database contents

@pytest.fixture
def users():
    return [
        { "id": 1, "username": "alice", "email": "alice@example.com" },
        { "id": 2, "username": "bob", "email": "bob@example.com" },
        { "id": 3, "username": "charlie", "email": "charlie@example.com" },
        { "id": 4, "username": "david", "email": "david@example.com" },
        { "id": 5, "username": "eve", "email": "eve@example.com" },
    ]

@pytest.fixture
def get_user(users):
    def _get_user(id: int) -> dict:
        return [ a for a in users if a["id"] == id ][0]
    return _get_user

# Set up database

@pytest.fixture(autouse=True)
def setup(session, users):
    """Setup initial test data in database."""

    # Create accounts, with passwords equal to index (e.g. password1, password2, etc)
    for i, user in enumerate(users):
        db_user = DBUser(**user, hashed_password=f"password{i+1}")
        session.add(db_user)

    session.commit()