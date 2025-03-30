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
    response = client.get("/boards/3/items", headers=auth_headers(2))
    assert response.json() == {
        "metadata": { "count": 1 },
        "items": [ get_item(8) ]
    }
    assert response.status_code == 200

def test_get_private_items_unauthorized(client, auth_headers, exception):
    response = client.get("/boards/3/items", headers=auth_headers(4)) # user 4 should have no knowledge of board 3
    assert response.json() == exception("entity_not_found", "Unable to find board with id=3")
    assert response.status_code == 404