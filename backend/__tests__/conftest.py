import pytest

from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient

from backend import app, auth
from backend.dependencies import get_session, name_to_identifier
from backend.database import schema
from backend.database.schema import *

from backend.__tests__ import mock

from PIL import Image
import os
from random import random

from backend.utils import email_handler, rate_limiter

# Essential fixtures

@pytest.fixture
def session(monkeypatch):
    monkeypatch.setattr(schema, 'gen_uuid', mock.uuid)
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
    monkeypatch.setattr(auth, "hash_password", mock.hash_password)
    monkeypatch.setattr(auth, "check_password", mock.check_password)
    monkeypatch.setattr(email_handler, "send_verification_email", lambda a, v: mock.black_hole)
    monkeypatch.setattr(email_handler, "send_editor_invitation_email", lambda v, i, e: mock.black_hole)
    monkeypatch.setattr(rate_limiter, 'KEY_LIMITS', mock.KEY_LIMITS)
    
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

@pytest.fixture
def static_path():
    return os.path.join(os.getcwd(), '__tests__', 'media', 'static')

# Initial database contents

@pytest.fixture
def accounts():
    return [
        { "username": "alice", "email": "alice@example.com", "profile_image": None, "display_name": "Alice" },
        { "username": "bob", "email": "bob@example.com", "profile_image": None, "display_name": None },
        { "username": "charlie", "email": "charlie@example.com", "profile_image": None, "display_name": None },
        { "username": "david", "email": "david@example.com", "profile_image": None, "display_name": None },
        { "username": "eve", "email": "eve@example.com", "profile_image": None, "display_name": None },
    ]

@pytest.fixture
def boards():
    return [
        { "name": "parent", "icon": "earth", "owner_id": 1, "public": True },
        { "name": "child", "icon": "mountain", "owner_id": 1, "public": True },
        { "name": "other", "icon": "beaker", "owner_id": 2, "public": False },
    ]

@pytest.fixture
def editors(): # board_ids and account_ids
    return { 1: [2], 2: [3], 3: [1, 3] }

@pytest.fixture
def items():
    return [
        { "board_id": 1, "list_id": None, "position": "0,0", "index": None, "pin": None, "type": "note", "text": "Test Note" }, # 1
        { "board_id": 2, "list_id": None, "position": "0,0", "index": None, "pin": None, "type": "list", "title": "Test List" },
        { "board_id": 2, "list_id": 2, "position": None, "index": 0, "pin": None, "type": "note", "text": "List Item 1" },
        { "board_id": 2, "list_id": 2, "position": None, "index": 1, "pin": None, "type": "link", "title": "List Item 2 (board link)", "url": "/boards/1" },
        { "board_id": 1, "list_id": None, "position": "350,0", "index": None, "pin": None, "type": "todo", "title": "Todo List 1" }, # 5
        { "board_id": 2, "list_id": None, "position": "350,0", "index": None, "pin": None, "type": "todo", "title": "Todo List 2" },
        { "board_id": 1, "list_id": None, "position": "0,250", "index": None, "pin": None, "type": "link", "title": "External Link", "url": "https://www.example.com/" },
        { "board_id": 3, "list_id": None, "position": "0,0", "index": None, "pin": None, "type": "note", "text": "Private Note" },
        { "board_id": 2, "list_id": None, "position": "0,500", "index": None, "pin": None, "type": "list", "title": "Test List 2" },
        { "board_id": 2, "list_id": 9, "position": None, "index": 0, "pin": None, "type": "note", "text": "List Item 3" }, # 10
        { "board_id": 2, "list_id": None, "position": "0,-300", "index": None, "pin": None, "type": "note", "text": "Board 2 Item" },
    ]

@pytest.fixture
def todo_items():
    return [
        { "list_id": 5, "text": "Item 1", "done": True, "link": None }, # 1
        { "list_id": 5, "text": "Item 2", "done": False, "link": None },
        { "list_id": 5, "text": "Item 3", "done": False, "link": None },
        { "list_id": 6, "text": "Item 1", "done": True, "link": None },
        { "list_id": 6, "text": "Item 2", "done": True, "link": None }, # 5
        { "list_id": 6, "text": "Item 3", "done": False, "link": None },
    ]

@pytest.fixture
def pins():
    return [
        { "board_id": 2, "item_id": 2, "label": "List 1", "compass": True, "connections": [ 2 ] },
        { "board_id": 2, "item_id": 9, "label": "List 2", "compass": False, "connections": [ 1 ] },
        { "board_id": 2, "item_id": 11, "label": None, "compass": False, "connections": [  ] },
    ]

# Set up database

@pytest.fixture(autouse=True)
def setup(session, accounts, boards, editors, items, todo_items, pins):
    """Setup initial test data in database."""

    # Create accounts, with passwords equal to index (e.g. password1, password2, etc)
    # Assume they all have verified emails
    mock.last_uuid = mock.OFFSETS['account']
    db_accounts = {}
    for i, account in enumerate(accounts):
        db_account = DBAccount(**account, hashed_password=f"hashed_password{i+1}")
        db_accounts[mock.to_uuid(i + 1, 'account')] = db_account
        session.add(db_account)
    session.commit()

    mock.last_uuid = mock.OFFSETS['permission']
    for account in db_accounts.values():
        session.refresh(account)
        account.permission = DBPermission( account_id=account.id )
        session.add(account)
    session.commit()

    mock.last_uuid = mock.OFFSETS['customer']
    for account in db_accounts.values():
        session.refresh(account)
        account.customer = DBCustomer( account_id=account.id )
        session.add(account)
    session.commit()

    # Create boards
    mock.last_uuid = mock.OFFSETS['board']
    for i, board in enumerate(boards):
        db_board = DBBoard(**board)
        db_board.owner_id = mock.to_uuid(board['owner_id'], 'account')
        db_board.identifier = board['identifier'] if 'identifier' in board else name_to_identifier(board['name'])
        for editor_id in editors[i + 1]:
            db_board.editors.append(db_accounts[mock.to_uuid(editor_id, 'account')])
        session.add(db_board)
    session.commit()

    # Create items
    mock.last_uuid = mock.OFFSETS['item']
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
        db_item.board_id = mock.to_uuid(item['board_id'], 'board')
        db_item.list_id = mock.to_uuid(item['list_id'], 'item') if item['list_id'] is not None else None
        db_items[mock.to_uuid(i + 1, 'item')] = db_item
        session.add(db_item)
    session.commit()

    # Create todo list items
    mock.last_uuid = mock.OFFSETS['sub_item']
    for i, item in enumerate(todo_items):
        db_todo_item = DBTodoItem(**item)
        db_todo_item.list_id = mock.to_uuid(item['list_id'], 'item')
        session.add(db_todo_item)
    session.commit()

    # Create pins
    mock.last_uuid = mock.OFFSETS['pin']
    db_pins: dict[str, DBPin] = {}
    for i, pin in enumerate(pins):
        p = pin.copy()
        del p['connections']
        p['item_id'] = mock.to_uuid(p['item_id'], 'item')
        p['board_id'] = mock.to_uuid(p['board_id'], 'board')
        db_pin = DBPin(**p)
        session.add(db_pin)
        db_pins[mock.to_uuid(i + 1, 'pin')] = db_pin
    session.commit()

    # Connect pins to items and each other
    for i, pin, in enumerate(pins):
        for conn_id in pin['connections']:
            db_pins[mock.to_uuid(i + 1, 'pin')].connections.append(db_pins[mock.to_uuid(conn_id, 'pin')])
    session.commit()

    # Promote users
    # Currently just have Eve as our super admin
    eve: DBAccount = db_accounts[mock.to_uuid(5, 'account')]
    eve.permission.role = "app_administrator"
    session.add(eve)
    session.add(eve.permission)
    session.commit()

    session.commit()

# Helpful methods

@pytest.fixture
def get_account(accounts):
    """Function to get an account by ID"""
    def _get_account(id: int) -> dict:
        account = accounts[id - 1].copy()
        account['id'] = mock.to_uuid(id, 'account')
        return account
    return _get_account

@pytest.fixture
def get_board(boards):
    """Function to get a board by ID"""
    def _get_board(id: int) -> dict:
        board = boards[id - 1].copy()
        board['id'] = mock.to_uuid(id, 'board')
        board['owner_id'] = mock.to_uuid(board['owner_id'], 'account')
        board['identifier'] = board['identifier'] if 'identifier' in board else name_to_identifier(board['name'])
        return board
    return _get_board

@pytest.fixture
def get_item(items, todo_items, get_item_pin):
    """Function to get an item by ID"""
    def _get_item(id: int, includeBoardId: bool = True) -> dict:
        item = items[id - 1].copy()
        # update IDs
        item['id'] = mock.to_uuid(id, 'item')
        item['board_id'] = mock.to_uuid(item['board_id'], 'board')
        item['list_id'] = mock.to_uuid(item['list_id'], 'item') if item['list_id'] is not None else None
        # Also populate contents
        item['pin'] = get_item_pin(id)
        if item['type'] == "todo":
            contents = []
            for i, t in enumerate(todo_items):
                todo_item = t.copy()
                if todo_item['list_id'] != id:
                    continue
                todo_item['id'] = mock.to_uuid(i + 1, 'sub_item')
                todo_item['list_id'] = mock.to_uuid(id, 'item')
                contents.append(todo_item)
            item['contents'] = { "metadata": { "count": len(contents) }, "items": contents }
        if item['type'] == "list":
            contents = []
            for i, li in enumerate(items):
                if li['list_id'] != id:
                    continue
                list_item = li.copy()
                list_item['id'] = mock.to_uuid(i + 1, 'item')
                list_item['list_id'] = mock.to_uuid(id, 'item')
                if includeBoardId:
                    list_item['board_id'] = mock.to_uuid(list_item['board_id'], 'board')
                else:
                    del list_item['board_id']
                contents.append(list_item)
            item['contents'] = { "metadata": { "count": len(contents) }, "items": sorted(contents, key=lambda i: i['index']) }
        # Remove board ID if not asked for
        if not includeBoardId:
            del item['board_id']
        return item
    return _get_item

@pytest.fixture
def get_response_account(get_account):
    """Function to get an account's response model by ID"""
    def _get_response_account(id: int, profile_image: str | None = None) -> dict:
        base = get_account(id).copy()
        del base['email']
        base['profile_image'] = profile_image
        return base
    return _get_response_account

@pytest.fixture
def create_login(get_account):
    """Function to create a Login object (email and password) for this account id"""
    def _create_login(id: int) -> dict:
        email: str = get_account(id)["email"]
        password: str = "password" + str(id)
        return { "identifier": email, "password": password }
    return _create_login

@pytest.fixture
def auth_headers(client, create_login):
    def _auth_headers(id: int):
        response = client.post("/auth/token", data=create_login(id))
        assert response.status_code == 200
        token = response.json()["access_token"]
        return { "Authorization": f"Bearer {token}" }
    return _auth_headers

@pytest.fixture
def login(create_login, form_headers):
    def _login(client, id: int): # takes in a client so we can save the cookie
        response = client.post("/auth/web/login", headers=form_headers, data=create_login(id))
        assert response.status_code == 204
        return response
    return _login

@pytest.fixture()
def def_item(items):
    """Function to create the default values added when creating an item with this configuration"""
    def _def_item(board_id: int) -> dict:
        return {
            "id": mock.to_uuid(len(items) + 1, 'item'),
            "board_id": mock.to_uuid(board_id, 'board'),
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
        pin = pins[id - 1].copy()
        pin['id'] = mock.to_uuid(id, 'pin')
        pin['item_id'] = mock.to_uuid(pin['item_id'], 'item')
        pin['board_id'] = mock.to_uuid(pin['board_id'], 'board')
        pin['connections'] = [ mock.to_uuid(c, 'pin') for c in pin['connections'] ]
        return pin
    return _get_pin

@pytest.fixture()
def get_item_pin(pins):
    """Function that returns the pin object attached to an Item, or None"""
    def _get_item_pin(item_id: int):
        for i, p in enumerate(pins):
            if p['item_id'] == item_id:
                pin = p.copy()
                pin['id'] = mock.to_uuid(i + 1, 'pin')
                pin['item_id'] = mock.to_uuid(item_id, 'item')
                pin['board_id'] = mock.to_uuid(pin['board_id'], 'board')
                pin['connections'] = [ mock.to_uuid(c, 'pin') for c in pin['connections'] ]
                return pin
        return None
    return _get_item_pin

@pytest.fixture()
def create_image():
    """Function that takes in dimensions and creates a PNG image"""
    def _create_image(w: int, h: int, randomized: bool = False) -> Image:
        image = Image.new('RGB', (w, h), color='black')
        # set randomized contents to minimize compression
        if randomized:
            for x in range(w):
                for y in range(h):
                    image.putpixel((x, y), (int(random() * 255), int(random() * 255), int(random() * 255)))
        # put white pixels in each corner to ensure the image gets resized correctly. draw a 2x2 to ensure they stay there when shrunk
        square = lambda s: [ (s[0], s[1]), (s[0]+1, s[1]), (s[0], s[1]+1), (s[0]+1, s[1]+1) ]
        coords = square((0, 0)) + square((w-2, 0)) + square((0, h-2)) + square((w-2, h-2))
        for c in coords:
            image.putpixel(c, (255,255,255))
        return image
    return _create_image