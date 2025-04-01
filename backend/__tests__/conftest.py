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

@pytest.fixture
def items():
    return [
        { "id": 1, "board_id": 1, "list_id": None, "position": "0,0", "index": None, "pin": None, "type": "note", "text": "Test Note", "size": "300,200" },
        { "id": 2, "board_id": 2, "list_id": None, "position": "0,0", "index": None, "pin": None, "type": "list", "title": "Test List" },
        { "id": 3, "board_id": 2, "list_id": 2, "position": None, "index": 0, "pin": None, "type": "note", "text": "List Item 1", "size": "300,200" },
        { "id": 4, "board_id": 2, "list_id": 2, "position": None, "index": 1, "pin": None, "type": "link", "title": "List Item 2 (board link)", "url": "/boards/1" },
        { "id": 5, "board_id": 1, "list_id": None, "position": "350,0", "index": None, "pin": None, "type": "todo", "title": "Todo List 1" },
        { "id": 6, "board_id": 2, "list_id": None, "position": "350,0", "index": None, "pin": None, "type": "todo", "title": "Todo List 2" },
        { "id": 7, "board_id": 1, "list_id": None, "position": "0,250", "index": None, "pin": None, "type": "link", "title": "External Link", "url": "https://www.example.com/" },
        { "id": 8, "board_id": 3, "list_id": None, "position": "0,0", "index": None, "pin": None, "type": "note", "text": "Private Note", "size": "300,200" },
        { "id": 9, "board_id": 2, "list_id": None, "position": "0,500", "index": None, "pin": None, "type": "list", "title": "Test List 2" },
        { "id": 10, "board_id": 2, "list_id": 9, "position": None, "index": 0, "pin": None, "type": "note", "text": "List Item 3", "size": "300,200" },
        { "id": 11, "board_id": 2, "list_id": None, "position": "0,-300", "index": None, "pin": None, "type": "note", "text": "Board 2 Item", "size": "300,200" },
    ]

@pytest.fixture
def todo_items():
    return [
        { "id": 1, "list_id": 5, "text": "Item 1", "done": True, "link": None },
        { "id": 2, "list_id": 5, "text": "Item 2", "done": False, "link": None },
        { "id": 3, "list_id": 5, "text": "Item 3", "done": False, "link": None },
        { "id": 4, "list_id": 6, "text": "Item 1", "done": True, "link": None },
        { "id": 5, "list_id": 6, "text": "Item 2", "done": True, "link": None },
        { "id": 6, "list_id": 6, "text": "Item 3", "done": False, "link": None },
    ]

@pytest.fixture
def pins():
    return [
        { "id": 1, "board_id": 2, "item_id": 2, "label": "List 1", "compass": True, "connections": [ 2 ] },
        { "id": 2, "board_id": 2, "item_id": 9, "label": "List 2", "compass": False, "connections": [ 1 ] },
        { "id": 3, "board_id": 2, "item_id": 11, "label": None, "compass": False, "connections": [  ] },
    ]

# Set up database

@pytest.fixture(autouse=True)
def setup(session, users, boards, editors, items, todo_items, pins):
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
        for editor_id in editors[db_board.id]:
            db_board.editors.append(db_users[editor_id])
        session.add(db_board)

    # Create items
    db_items = {}
    for i, item in enumerate(items):
        db_item = None
        match item['type']:
            case "note":
                db_item = DBItemNote(**item)
            case "link":
                db_item = DBItemLink(**item)
            case "media":
                db_item = DBItemMedia(**item)
            case "todo":
                db_item = DBItemTodo(**item)
            case "list":
                db_item = DBItemList(**item)
        if db_item is None:
            raise ValueError(f"'{item['type']}' could not be matched to an item type.")
        db_items[db_item.id] = db_item
        session.add(db_item)

    # Create todo list items
    for i, item in enumerate(todo_items):
        db_todo_item = DBTodoItem(**item)
        session.add(db_todo_item)

    # Create pins
    db_pins: dict[int, DBPin] = {}
    for i, pin in enumerate(pins):
        d = pin.copy()
        del d['connections']
        db_pin = DBPin(**d)
        session.add(db_pin)
        db_pins[db_pin.id] = db_pin

    # Connect pins to items and each other
    for i, pin, in enumerate(pins):
        db_items
        for conn_id in pin['connections']:
            db_pins[i+1].connections.append(db_pins[conn_id])

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
def get_item(items, todo_items, get_item_pin):
    """Function to get an item by ID"""
    def _get_item(id: int, includeBoardId: bool = True) -> dict:
        item = [ i for i in items if i["id"] == id ][0]
        # Also populate contents
        item['pin'] = get_item_pin(id)
        if item['type'] == "todo":
            contents = sorted([ i for i in todo_items if i['list_id'] == id ], key=lambda i: i['id'])
            item['contents'] = { "metadata": { "count": len(contents) }, "items": contents }
        if item['type'] == "list":
            contents = sorted([ i for i in items if i['list_id'] == id ], key=lambda i: i['index'])
            if not includeBoardId:
                for i in contents:
                    del i['board_id']
            item['contents'] = { "metadata": { "count": len(contents) }, "items": contents }
        # Remove board ID if not asked for
        if not includeBoardId:
            del item['board_id']
        return item
    return _get_item

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

@pytest.fixture()
def def_item(items):
    """Function to create the default values added when creating an item with this configuration"""
    def _def_item(board_id: int) -> dict:
        return {
            "id": len(items) + 1,
            "board_id": board_id,
            "list_id": None,
            "position": "0,0",
            "index": None,
            "pin": None,
        }
    return _def_item

@pytest.fixture()
def empty_collection():
    """Function to generate an empty collection with this key"""
    def _empty_collection(list_key: str) -> dict:
        return {
            "metadata": { "count": 0 },
            list_key: []
        }
    return _empty_collection

@pytest.fixture
def get_pin(pins):
    """Function to get a pin by ID"""
    def _get_pin(id: int) -> dict:
        return [ p for p in pins if p["id"] == id ][0]
    return _get_pin

@pytest.fixture()
def get_item_pin(pins):
    """Function that returns the pin object attached to an Item, or None"""
    def _get_item_pin(item_id: int):
        for pin in pins:
            if pin['item_id'] == item_id:
                return pin
        return None
    return _get_item_pin