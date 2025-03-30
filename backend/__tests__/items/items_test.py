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