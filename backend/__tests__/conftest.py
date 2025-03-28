import pytest
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import declarative_base, sessionmaker
from starlette.testclient import TestClient

from backend import app, auth
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
    monkeypatch.setattr(auth, "hash_password", lambda p: "hashed_" + p)
    monkeypatch.setattr(auth, "check_password", lambda p, h: "hashed_" + p == h)
    
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

@pytest.fixture
def form_headers():
    return { "Content-Type": "application/x-www-form-urlencoded" }

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
def boards():
    return [
        { "id": 1, "name": "parent", "icon": "earth", "owner_id": 1, "public": True },
        { "id": 2, "name": "child", "icon": "mountain", "owner_id": 1, "public": True },
        { "id": 3, "name": "other", "icon": "beaker", "owner_id": 2, "public": False },
    ]

@pytest.fixture
def editors(): # board_ids and user_ids
    return { 1: [2], 2: [3], 3: [1, 3] }

# Set up database

@pytest.fixture(autouse=True)
def setup(session, users, boards, editors):
    """Setup initial test data in database."""

    # Create accounts, with passwords equal to index (e.g. password1, password2, etc)
    db_users = {}
    for i, user in enumerate(users):
        db_user = DBUser(**user, hashed_password=f"hashed_password{i+1}")
        db_users[db_user.id] = db_user
        session.add(db_user)

    # Create boards
    for i, board in enumerate(boards):
        db_board = DBBoard(**board)
        for editor in editors[db_board.id]:
            db_board.editors.append(db_users[editor])
        session.add(db_board)

    session.commit()

# Helpful methods

@pytest.fixture
def get_user(users):
    """Function to get a user by ID"""
    def _get_user(id: int) -> dict:
        return [ u for u in users if u["id"] == id ][0]
    return _get_user

@pytest.fixture
def get_board(boards):
    """Function to get a board by ID"""
    def _get_board(id: int) -> dict:
        return [ b for b in boards if b["id"] == id ][0]
    return _get_board

@pytest.fixture
def get_response_user(get_user):
    """Function to get a user's response model by ID"""
    def _get_response_user(id: int, profile_image: dict | None = None) -> dict:
        base = get_user(id)
        del base['email']
        base['profile_image'] = profile_image
        return base
    return _get_response_user

@pytest.fixture
def create_login(get_user):
    """Function to create a Login object (email and password) for this user id"""
    def _create_login(id: int) -> dict:
        email: str = get_user(id)["email"]
        password: str = "password" + str(id)
        return { "email": email, "password": password }
    return _create_login

@pytest.fixture
def auth_headers(client, create_login):
    def _auth_headers(id: int):
        response = client.post("/auth/login", data=create_login(id))
        assert response.status_code == 200
        token = response.json()["access_token"]
        return { "Authorization": f"Bearer {token}" }
    return _auth_headers

@pytest.fixture
def login_client(create_login, form_headers):
    def _login_client(client, id: int): # takes in a client so we can save the cookie
        response = client.post("/auth/login", headers=form_headers, data=create_login(id))
        assert response.status_code == 200
        token = response.json()["access_token"]
        return { "Authorization": f"Bearer {token}" }, response
    return _login_client