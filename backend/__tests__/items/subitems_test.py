"""Module for testing the item routes relating to subitems like todoitems and pins"""

def test_add_todo_item(client, auth_headers, get_item):
    item = { "list_id": 5, "text": "New Task", "link": "/boards/1/items/1", "done": False }
    updated_item = {
        "id": 7,
        **item,
    }
    response = client.post("/boards/1/items/todo", headers=auth_headers(1), json=item)
    assert response.json() == updated_item
    assert response.status_code == 201
    response = client.get("/boards/1/items/5")
    todo = get_item(5)
    todo['contents']['metadata']['count'] = 4
    todo['contents']['items'].append(updated_item)
    assert response.json() == todo
    assert response.status_code == 200

def test_add_todo_item_defaults(client, auth_headers, get_item):
    item = { "list_id": 5, "text": "New Task" }
    updated_item = {
        "id": 7,
        **item,
        "link": None,
        "done": False,
    }
    response = client.post("/boards/1/items/todo", headers=auth_headers(1), json=item)
    assert response.json() == updated_item
    assert response.status_code == 201
    response = client.get("/boards/1/items/5")
    todo = get_item(5)
    todo['contents']['metadata']['count'] = 4
    todo['contents']['items'].append(updated_item)
    assert response.json() == todo
    assert response.status_code == 200

def test_add_todo_item_wrong_board(client, auth_headers, exception):
    item = { "list_id": 5, "text": "New Task", "link": "/boards/2/items/2", "done": False }
    response = client.post("/boards/2/items/todo", headers=auth_headers(1), json=item)
    assert response.json() == exception("entity_not_found", "Unable to find item_todo with id=5")
    assert response.status_code == 404

def test_add_todo_item_to_404_todo(client, auth_headers, exception):
    item = { "list_id": 404, "text": "New Task", "link": "/boards/1/items/5", "done": False }
    response = client.post("/boards/1/items/todo", headers=auth_headers(1), json=item)
    assert response.json() == exception("entity_not_found", "Unable to find item_todo with id=404")
    assert response.status_code == 404

def test_add_todo_item_to_non_todo(client, auth_headers, exception):
    item = { "list_id": 1, "text": "New Task", "link": "/boards/1/items/5", "done": False }
    response = client.post("/boards/1/items/todo", headers=auth_headers(1), json=item)
    assert response.json() == exception("item_type_mismatch", "Item with id=1 has type 'note', but was treated as if it had type 'todo'")
    assert response.status_code == 418

def test_add_todo_item_unauthorized(client, auth_headers, exception):
    item = { "list_id": 5, "text": "New Task", "link": "/boards/1/items/1", "done": False }
    response = client.post("/boards/1/items/todo", headers=auth_headers(4), json=item)
    assert response.json() == exception("access_denied", "Access denied")
    assert response.status_code == 403

def test_update_todo_item(client, auth_headers, get_item):
    update = { "done": True }
    response = client.put("/boards/1/items/todo/3", headers=auth_headers(1), json=update)
    assert response.json() == { "id": 3, "list_id": 5, "text": "Item 3", "link": None, "done": True }
    assert response.status_code == 200
    response = client.get("/boards/1/items/5")
    todo = get_item(5)
    todo['contents']['items'][2]['done'] = True
    assert response.json() == todo
    assert response.status_code == 200

def test_update_404_todo_item(client, auth_headers, exception):
    update = { "done": True }
    response = client.put("/boards/1/items/todo/404", headers=auth_headers(1), json=update)
    assert response.json() == exception("entity_not_found", "Unable to find todo_item with id=404")
    assert response.status_code == 404

def test_update_todo_item_other_board(client, auth_headers, exception):
    update = { "done": True }
    response = client.put("/boards/2/items/todo/3", headers=auth_headers(1), json=update)
    assert response.json() == exception("entity_not_found", "Unable to find todo_item with id=3")
    assert response.status_code == 404

def test_update_todo_item_unauthorized(client, auth_headers, exception):
    update = { "done": True }
    response = client.put("/boards/1/items/todo/3", headers=auth_headers(4), json=update)
    assert response.json() == exception("access_denied", "Access denied")
    assert response.status_code == 403

def test_delete_todo_item(client, auth_headers, get_item):
    response = client.delete("/boards/1/items/todo/3", headers=auth_headers(1))
    assert response.status_code == 204
    response = client.get("/boards/1/items/5")
    todo = get_item(5)
    todo['contents']['metadata']['count'] = 2
    todo['contents']['items'].pop(2)
    assert response.json() == todo
    assert response.status_code == 200

def test_delete_404_todo_item(client, auth_headers, exception):
    response = client.delete("/boards/1/items/todo/404", headers=auth_headers(1))
    assert response.json() == exception("entity_not_found", "Unable to find todo_item with id=404")
    assert response.status_code == 404

def test_delete_todo_item_other_board(client, auth_headers, exception):
    response = client.delete("/boards/2/items/todo/3", headers=auth_headers(1))
    assert response.json() == exception("entity_not_found", "Unable to find todo_item with id=3")
    assert response.status_code == 404

def test_delete_todo_item_unauthorized(client, auth_headers, exception):
    response = client.delete("/boards/1/items/todo/3", headers=auth_headers(4))
    assert response.json() == exception("access_denied", "Access denied")
    assert response.status_code == 403

def test_create_pin(client, auth_headers):
    config = {
        'item_id': 6,
        'label': "Todo Pin",
        'compass': True,
    }
    updated = {
        **config,
        'id': 4,
        'board_id': 2,
        'connections': [],
    }
    response = client.post("/boards/2/items/pins", headers=auth_headers(1), json=config)
    assert response.json() == updated
    assert response.status_code == 201

def test_create_pin_defaults(client, auth_headers):
    config = {
        'item_id': 6,
    }
    updated = {
        **config,
        'id': 4,
        'board_id': 2,
        'connections': [],
        'label': None,
        'compass': False,
    }
    response = client.post("/boards/2/items/pins", headers=auth_headers(1), json=config)
    assert response.json() == updated
    assert response.status_code == 201

def test_create_pin_wrongboard(client, auth_headers, exception):
    config = {
        'item_id': 6,
    }
    response = client.post("/boards/1/items/pins", headers=auth_headers(1), json=config)
    assert response.json() == exception("entity_not_found", "Unable to find item with id=6")
    assert response.status_code == 404

def test_create_pin_404_item(client, auth_headers, exception):
    config = {
        'item_id': 404,
    }
    response = client.post("/boards/1/items/pins", headers=auth_headers(1), json=config)
    assert response.json() == exception("entity_not_found", "Unable to find item with id=404")
    assert response.status_code == 404

def test_create_pin_duplicate(client, auth_headers, exception):
    config = {
        'item_id': 2,
    }
    response = client.post("/boards/2/items/pins", headers=auth_headers(1), json=config)
    assert response.json() == exception("duplicate_entity", "Entity pin with item_id=2 already exists")
    assert response.status_code == 422

def test_update_pin(client, auth_headers, get_pin):
    update = { 'label': 'Updated' } # this pin has compass set to True which is good for testing since compass is set to false by default
    expected = get_pin(1).copy()
    expected['label'] = 'Updated'
    response = client.put("/boards/2/items/pins/1", headers=auth_headers(1), json=update)
    assert response.json() == expected
    assert response.status_code == 200

def test_update_404_pin(client, auth_headers, exception):
    update = { 'label': 'Updated' } # this pin has compass set to True which is good for testing since compass is set to false by default
    response = client.put("/boards/2/items/pins/404", headers=auth_headers(1), json=update)
    assert response.json() == exception('entity_not_found', 'Unable to find pin with id=404')
    assert response.status_code == 404

def test_update_pin_move(client, auth_headers, get_pin, get_item):
    update = { 'item_id': 6 } # this pin is on list 1 and connected to the one on list 2, we move to the todo list
    expected = get_pin(1).copy()
    expected['item_id'] = 6
    response = client.put("/boards/2/items/pins/1", headers=auth_headers(1), json=update)
    assert response.json() == expected
    assert response.status_code == 200
    # Make sure the relevant items are updated
    expected = get_item(2).copy()
    pin, expected['pin'] = expected['pin'], None
    response = client.get("/boards/2/items/2")
    assert response.json() == expected
    assert response.status_code == 200
    expected = get_item(6).copy()
    pin['item_id'] = 6
    expected['pin'] = pin
    response = client.get("/boards/2/items/6")
    assert response.json() == expected
    assert response.status_code == 200

def test_update_pin_move_404(client, auth_headers, exception, get_item):
    update = { 'item_id': 404 }
    response = client.put("/boards/2/items/pins/1", headers=auth_headers(1), json=update)
    assert response.json() == exception("entity_not_found", "Unable to find item with id=404")
    assert response.status_code == 404
    # Make sure the item still has the pin
    response = client.get("/boards/2/items/2")
    assert response.json() == get_item(2)
    assert response.status_code == 200

def test_update_pin_move_duplicate(client, auth_headers, exception, get_item):
    update = { 'item_id': 11 } # move to Board 2 Item which already has a pin
    response = client.put("/boards/2/items/pins/1", headers=auth_headers(1), json=update)
    assert response.json() == exception("duplicate_entity", "Entity pin with item_id=11 already exists")
    assert response.status_code == 422
    # Make sure the relevant items are unchanged
    response = client.get("/boards/2/items/2")
    assert response.json() == get_item(2)
    assert response.status_code == 200
    response = client.get("/boards/2/items/11")
    assert response.json() == get_item(11)
    assert response.status_code == 200

def test_update_pin_move_between_boards(client, auth_headers, exception, get_item):
    update = { 'item_id': 1 } # move to Board 2 Item which already has a pin
    response = client.put("/boards/2/items/pins/1", headers=auth_headers(1), json=update)
    assert response.json() == exception("entity_not_found", "Unable to find item with id=1")
    assert response.status_code == 404
    # Make sure the relevant items are unchanged
    response = client.get("/boards/2/items/2")
    assert response.json() == get_item(2)
    assert response.status_code == 200
    response = client.get("/boards/1/items/1")
    assert response.json() == get_item(1)
    assert response.status_code == 200

def test_delete_pin(client, auth_headers, get_item):
    response = client.delete("/boards/2/items/pins/3", headers=auth_headers(1))
    assert response.status_code == 204
    # Make sure it's gone
    expected = get_item(11).copy()
    expected['pin'] = None
    response = client.get("/boards/2/items/11")
    assert response.json() == expected
    assert response.status_code == 200

def test_delete_pin_with_connection(client, auth_headers, get_item):
    response = client.delete("/boards/2/items/pins/1", headers=auth_headers(1))
    assert response.status_code == 204
    # Make sure it's gone, and the other pin doesn't have a connection
    expected = get_item(2).copy()
    expected['pin'] = None
    response = client.get("/boards/2/items/2")
    assert response.json() == expected
    assert response.status_code == 200
    expected = get_item(9).copy()
    expected['pin']['connections'].remove(1)
    response = client.get("/boards/2/items/9")
    assert response.json() == expected
    assert response.status_code == 200

def test_delete_404_pin(client, auth_headers, exception):
    response = client.delete("/boards/2/items/pins/404", headers=auth_headers(1))
    assert response.json() == exception("entity_not_found", "Unable to find pin with id=404")
    assert response.status_code == 404