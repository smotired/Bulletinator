"""A script that inserts a bunch of default data into the database. Not used as part of the program. Should be run from a blank database."""

import requests

HOST = "http://localhost:8000"
URL = lambda path: HOST + path

FORM_HEADERS = {
    "content-type": "application/x-www-form-urlencoded"
}

ACCOUNTS = [
    { "username": "john", "email": "john@example.com", "password": "pw1" },
    { "username": "jane", "email": "jane@example.com", "password": "pw2" },
    { "username": "jordan", "email": "jordan@example.com", "password": "pw3" },
]
accounts = {}

def AUTH_HEADERS(id: int) -> dict:
    account = ACCOUNTS[id - 1]
    form = { "identifier": account['email'], "password": account['password'] }
    response = requests.post(URL("/auth/token"), headers=FORM_HEADERS, data=form)
    access_token = response.json()['access_token']
    return { "Authorization": f"Bearer {access_token}" }

# Register all accounts
for i, form in enumerate(ACCOUNTS):
    response = requests.post(URL("/auth/registration"), headers=FORM_HEADERS, data=form)
    accounts[i+1] = response.json()

BOARD_CREATIONS = [
    { "owner_id": 1, "name": "Main Board", "public": True },
    { "owner_id": 1, "name": "Child Board", "icon": "sun", "public": False },
    { "owner_id": 2, "name": "Other Board", "identifier": "other", "icon": "default", "public": True },
]
boards = {}

for i, board in enumerate(BOARD_CREATIONS):
    config = board.copy()
    del config['owner_id']
    response = requests.post(URL("/boards"), headers=AUTH_HEADERS(board['owner_id']), json=config)
    boards[i+1] = response.json()

# currently all the items are on board 1 so we dont have to worry about that logic

ITEM_CREATIONS = [
    { "position": "0,0", "type": "note", "text": "Example note" },
    { "position": "0,250", "type": "link", "title": "Link to Child Board", "url": "/boards/2" },
    { "position": "350,0", "type": "list", "title": "Example List" },
    { "list_id": 3, "type": "note", "text": "List item 1" },
    { "list_id": 3, "type": "note", "text": "List item 2" },
    { "position": "700,0", "type": "todo", "title": "Todo List" },
]
items = {} # save the objects that are created so we can reference with IDs

ah = AUTH_HEADERS(1)
board_id = boards[1]['id']
for i, item in enumerate(ITEM_CREATIONS):
    config = item.copy()
    if 'list_id' in item:
        config['list_id'] = items[item['list_id']]['id']
    response = requests.post(URL(f"/boards/{board_id}/items"), headers=ah, json=config)
    items[i+1] = response.json()

# pins are also on board 1

PIN_CREATIONS = [
    { "item_id": 1, "label": "Home", "compass": True },
    { "item_id": 2, "label": "List", "compass": True },
    { "item_id": 5 },
]
pins = {}

ah = AUTH_HEADERS(1)
board_id = boards[1]['id']
for i, pin in enumerate(PIN_CREATIONS):
    config = pin.copy()
    config['item_id'] = items[pin['item_id']]['id']
    response = requests.post(URL(f"/boards/{board_id}/items/pins"), headers=ah, json=config)
    pins[i+1] = response.json()

EDITORS = { # mapping of board ids to the list of users that can edit them
    3: [1]
}

ah = AUTH_HEADERS(2)
board_id = boards[3]['id']
account_id = accounts[1]['id']
res = requests.put(URL(F"/boards/{board_id}/editors/{account_id}"), headers=ah)
print(res.json())

PIN_CONNECTIONS = [ # ONE WAY - BACKEND CREATES OTHER WAY AUTOMATICALLY
    (1, 2)
]

ah = AUTH_HEADERS(1)
board_id = boards[1]['id']
p1i, p2i = pins[1]['id'], pins[2]['id']
res = requests.put(URL(f"/boards/{board_id}/items/pins/connect?p1={p1i}&p2={p2i}"), headers=ah)
print(res.json())