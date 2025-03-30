"""Module for testing the item routes"""

def test_get_items1(client, get_item):
    response = client.get("/boards/1/items")
    assert response.json() == {
        "metadata": { "count": 3 },
        "items": [ get_item(1), get_item(5), get_item(7) ]
    }
    assert response.status_code == 200

def test_get_items2(client, get_item):
    response = client.get("/boards/2/items")
    assert response.json() == {
        "metadata": { "count": 2 },
        "items": [ get_item(2), get_item(6) ]
    }
    assert response.status_code == 200

def test_get_private_items(client, auth_headers, get_item):
    response = client.get("/boards/3/items", headers=auth_headers(3))
    assert response.json() == {
        "metadata": { "count": 1 },
        "items": [ get_item(8) ]
    }
    assert response.status_code == 200

def test_get_private_items_unauthorized(client, auth_headers, exception):
    response = client.get("/boards/3/items", headers=auth_headers(4)) # user 4 should have no knowledge of board 3
    assert response.json() == exception("entity_not_found", "Unable to find board with id=3")
    assert response.status_code == 404

def test_get_item(client, get_item):
    response = client.get("/boards/1/items/1")
    assert response.json() == get_item(1)
    assert response.status_code == 200

def test_get_404_item(client, exception):
    response = client.get("/boards/1/items/404")
    assert response.json() == exception("entity_not_found", "Unable to find item with id=404")
    assert response.status_code == 404

def test_get_private_item(client, auth_headers, get_item):
    response = client.get("/boards/3/items/8", headers=auth_headers(3))
    assert response.json() == get_item(8)
    assert response.status_code == 200

def test_get_private_item_unauthorized(client, auth_headers, exception):
    response = client.get("/boards/3/items/8", headers=auth_headers(4))
    assert response.json() == exception("entity_not_found", "Unable to find board with id=3")
    assert response.status_code == 404

def test_get_item_on_different_board(client, exception):
    response = client.get("/boards/2/items/1")
    assert response.json() == exception("entity_not_found", "Unable to find item with id=1")
    assert response.status_code == 404

def test_get_item_link(client, get_item):
    response = client.get("/boards/1/items/1")
    assert response.json() == get_item(1)
    assert response.status_code == 200

def test_get_item_todo(client, get_item):
    response = client.get("/boards/1/items/5")
    assert response.json() == get_item(5)
    assert response.status_code == 200

def test_get_item_list(client, get_item):
    response = client.get("/boards/2/items/2")
    assert response.json() == get_item(2)
    assert response.status_code == 200

def test_create_item(client, auth_headers, get_item):
    item = {
        "list_id": None,
        "position": "200,200",
        "index": None,
        "type": "note",
        "text": "Created Note",
        "size": "300,200"
    }
    response = client.post("/boards/1/items", headers=auth_headers(1), json=item)
    updated_item = {
        "id": 9,
        "board_id": 1,
        **item,
    }
    assert response.json() == updated_item
    assert response.status_code == 201
    response = client.get("/boards/1/items")
    assert response.json() == {
        "metadata": { "count": 4 },
        "items": [ get_item(1), get_item(5), get_item(7), updated_item ]
    }
    assert response.status_code == 200

def test_create_item_as_viewer(client, auth_headers, exception):
    item = {
        "list_id": None,
        "position": "200,200",
        "index": None,
        "type": "note",
        "text": "Created Note",
        "size": "300,200"
    }
    response = client.post("/boards/1/items", headers=auth_headers(3), json=item)
    assert response.json() == exception("access_denied", "Access denied")
    assert response.status_code == 403

def test_create_invalid_item(client, auth_headers, exception):
    item = { "type": "foo" }
    response = client.post("/boards/1/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("invalid_item_type", "Item type 'foo' is not valid")
    assert response.status_code == 422

def test_create_item_default_values(client, auth_headers, exception):
    item = {
        "type": "note",
        "text": "Created Note",
    }
    response = client.post("/boards/1/items", headers=auth_headers(1), json=item)
    assert response.json() == {
        "id": 9,
        "board_id": 1,
        "list_id": None,
        "position": "0,0",
        "index": None,
        **item,
        "size": "300,200",
    }
    assert response.status_code == 201

def test_create_private_item(client, auth_headers):
    item = {
        "type": "note",
        "text": "Private Note",
    }
    response = client.post("/boards/3/items", headers=auth_headers(3), json=item)
    assert response.json() == {
        "id": 9,
        "board_id": 3,
        "list_id": None,
        "position": "0,0",
        "index": None,
        **item,
        "size": "300,200",
    }
    assert response.status_code == 201


def test_create_private_item_unauthorized(client, auth_headers, exception):
    item = {
        "type": "note",
        "text": "Illegal Note",
    }
    response = client.post("/boards/3/items", headers=auth_headers(4), json=item)
    assert response.json() == exception("entity_not_found", "Unable to find board with id=3")
    assert response.status_code == 404

def test_create_item_missing_fields(client, auth_headers, exception):
    item = { "type": "note" }
    response = client.post("/boards/1/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("missing_item_fields", "Item type 'note' was missing the following fields: text")
    assert response.status_code == 422