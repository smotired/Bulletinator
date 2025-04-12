"""Module for testing the item routes relating to subitems like todoitems and pins"""

from backend.__tests__ import mock

def test_add_todo_item(client, auth_headers, todo_items, get_item):
    item = { "list_id": mock.to_uuid(5, 'item'), "text": "New Task", "link": f"/boards/{mock.to_uuid(1, 'board')}/items/{mock.to_uuid(1, 'item')}", "done": False }
    updated_item = {
        "id": mock.to_uuid(7, 'sub_item'),
        **item,
    }
    mock.last_uuid = mock.OFFSETS['sub_item'] + len(todo_items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items/todo", headers=auth_headers(1), json=item)
    assert response.json() == updated_item
    assert response.status_code == 201
    response = client.get(f"/boards/{mock.to_uuid(1, 'board')}/items/{mock.to_uuid(5, 'item')}")
    todo = get_item(5)
    todo['contents']['metadata']['count'] = 4
    todo['contents']['items'].append(updated_item)
    assert response.json() == todo
    assert response.status_code == 200

def test_add_todo_item_defaults(client, auth_headers, todo_items, get_item):
    item = { "list_id": mock.to_uuid(5, 'item'), "text": "New Task" }
    updated_item = {
        "id": mock.to_uuid(7, 'sub_item'),
        **item,
        "link": None,
        "done": False,
    }
    mock.last_uuid = mock.OFFSETS['sub_item'] + len(todo_items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items/todo", headers=auth_headers(1), json=item)
    assert response.json() == updated_item
    assert response.status_code == 201
    response = client.get(f"/boards/{mock.to_uuid(1, 'board')}/items/{mock.to_uuid(5, 'item')}")
    todo = get_item(5)
    todo['contents']['metadata']['count'] = 4
    todo['contents']['items'].append(updated_item)
    assert response.json() == todo
    assert response.status_code == 200

def test_add_todo_item_wrong_board(client, auth_headers, todo_items, exception):
    item = { "list_id": mock.to_uuid(5, 'item'), "text": "New Task", "link": f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(2, 'item')}", "done": False }
    mock.last_uuid = mock.OFFSETS['sub_item'] + len(todo_items)
    response = client.post(f"/boards/{mock.to_uuid(2, 'board')}/items/todo", headers=auth_headers(1), json=item)
    assert response.json() == exception("entity_not_found", f"Unable to find item_todo with id={mock.to_uuid(5, 'item')}")
    assert response.status_code == 404

def test_add_todo_item_to_404_todo(client, auth_headers, todo_items, exception):
    item = { "list_id": mock.to_uuid(404, 'item'), "text": "New Task", "link": f"/boards/{mock.to_uuid(1, 'board')}/items/{mock.to_uuid(5, 'item')}", "done": False }
    mock.last_uuid = mock.OFFSETS['sub_item'] + len(todo_items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items/todo", headers=auth_headers(1), json=item)
    assert response.json() == exception("entity_not_found", f"Unable to find item_todo with id={mock.to_uuid(404, 'item')}")
    assert response.status_code == 404

def test_add_todo_item_to_non_todo(client, auth_headers, todo_items, exception):
    item = { "list_id": mock.to_uuid(1, 'item'), "text": "New Task", "link": f"/boards/{mock.to_uuid(1, 'board')}/items/{mock.to_uuid(5, 'item')}", "done": False }
    mock.last_uuid = mock.OFFSETS['sub_item'] + len(todo_items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items/todo", headers=auth_headers(1), json=item)
    assert response.json() == exception("item_type_mismatch", f"Item with id={mock.to_uuid(1, 'item')} has type 'note', but was treated as if it had type 'todo'")
    assert response.status_code == 418

def test_add_todo_item_unauthorized(client, auth_headers, todo_items, exception):
    item = { "list_id": mock.to_uuid(5, 'item'), "text": "New Task", "link": f"/boards/{mock.to_uuid(1, 'board')}/items/{mock.to_uuid(1, 'item')}", "done": False }
    mock.last_uuid = mock.OFFSETS['sub_item'] + len(todo_items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items/todo", headers=auth_headers(4), json=item)
    assert response.json() == exception("access_denied", "Access denied")
    assert response.status_code == 403

def test_update_todo_item(client, auth_headers, get_item):
    update = { "done": True }
    response = client.put(f"/boards/{mock.to_uuid(1, 'board')}/items/todo/{mock.to_uuid(3, 'sub_item')}", headers=auth_headers(1), json=update)
    assert response.json() == { "id": mock.to_uuid(3, 'sub_item'), "list_id": mock.to_uuid(5, 'item'), "text": "Item 3", "link": None, "done": True }
    assert response.status_code == 200
    response = client.get(f"/boards/{mock.to_uuid(1, 'board')}/items/{mock.to_uuid(5, 'item')}")
    todo = get_item(5)
    todo['contents']['items'][2]['done'] = True
    assert response.json() == todo
    assert response.status_code == 200

def test_update_404_todo_item(client, auth_headers, exception):
    update = { "done": True }
    response = client.put(f"/boards/{mock.to_uuid(1, 'board')}/items/todo/{mock.to_uuid(404, 'sub_item')}", headers=auth_headers(1), json=update)
    assert response.json() == exception("entity_not_found", f"Unable to find todo_item with id={mock.to_uuid(404, 'sub_item')}")
    assert response.status_code == 404

def test_update_todo_item_other_board(client, auth_headers, exception):
    update = { "done": True }
    response = client.put(f"/boards/{mock.to_uuid(2, 'board')}/items/todo/{mock.to_uuid(3, 'sub_item')}", headers=auth_headers(1), json=update)
    assert response.json() == exception("entity_not_found", f"Unable to find todo_item with id={mock.to_uuid(3, 'sub_item')}")
    assert response.status_code == 404

def test_update_todo_item_unauthorized(client, auth_headers, exception):
    update = { "done": True }
    response = client.put(f"/boards/{mock.to_uuid(1, 'board')}/items/todo/{mock.to_uuid(3, 'sub_item')}", headers=auth_headers(4), json=update)
    assert response.json() == exception("access_denied", "Access denied")
    assert response.status_code == 403

def test_delete_todo_item(client, auth_headers, get_item):
    response = client.delete(f"/boards/{mock.to_uuid(1, 'board')}/items/todo/{mock.to_uuid(3, 'sub_item')}", headers=auth_headers(1))
    assert response.status_code == 204
    response = client.get(f"/boards/{mock.to_uuid(1, 'board')}/items/{mock.to_uuid(5, 'item')}")
    todo = get_item(5)
    todo['contents']['metadata']['count'] = 2
    todo['contents']['items'].pop(2)
    assert response.json() == todo
    assert response.status_code == 200

def test_delete_404_todo_item(client, auth_headers, exception):
    response = client.delete(f"/boards/{mock.to_uuid(1, 'board')}/items/todo/{mock.to_uuid(404, 'sub_item')}", headers=auth_headers(1))
    assert response.json() == exception("entity_not_found", f"Unable to find todo_item with id={mock.to_uuid(404, 'sub_item')}")
    assert response.status_code == 404

def test_delete_todo_item_other_board(client, auth_headers, exception):
    response = client.delete(f"/boards/{mock.to_uuid(2, 'board')}/items/todo/{mock.to_uuid(3, 'sub_item')}", headers=auth_headers(1))
    assert response.json() == exception("entity_not_found", f"Unable to find todo_item with id={mock.to_uuid(3, 'sub_item')}")
    assert response.status_code == 404

def test_delete_todo_item_unauthorized(client, auth_headers, exception):
    response = client.delete(f"/boards/{mock.to_uuid(1, 'board')}/items/todo/{mock.to_uuid(3, 'sub_item')}", headers=auth_headers(4))
    assert response.json() == exception("access_denied", "Access denied")
    assert response.status_code == 403

def test_create_pin(client, pins, auth_headers):
    config = {
        'item_id': mock.to_uuid(6, 'item'),
        'label': "Todo Pin",
        'compass': True,
    }
    updated = {
        **config,
        'id': mock.to_uuid(4, 'pin'),
        'board_id': mock.to_uuid(2, 'board'),
        'connections': [],
    }
    mock.last_uuid = mock.OFFSETS['pin'] + len(pins)
    response = client.post(f"/boards/{mock.to_uuid(2, 'board')}/items/pins", headers=auth_headers(1), json=config)
    assert response.json() == updated
    assert response.status_code == 201

def test_create_pin_defaults(client, auth_headers, pins):
    config = {
        'item_id': mock.to_uuid(6, 'item'),
    }
    updated = {
        **config,
        'id': mock.to_uuid(4, 'pin'),
        'board_id': mock.to_uuid(2, 'board'),
        'connections': [],
        'label': None,
        'compass': False,
    }
    mock.last_uuid = mock.OFFSETS['pin'] + len(pins)
    response = client.post(f"/boards/{mock.to_uuid(2, 'board')}/items/pins", headers=auth_headers(1), json=config)
    assert response.json() == updated
    assert response.status_code == 201

def test_create_pin_wrongboard(client, auth_headers, pins, exception):
    config = {
        'item_id': mock.to_uuid(6, 'item'),
    }
    mock.last_uuid = mock.OFFSETS['pin'] + len(pins)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items/pins", headers=auth_headers(1), json=config)
    assert response.json() == exception("entity_not_found", f"Unable to find item with id={mock.to_uuid(6, 'item')}")
    assert response.status_code == 404

def test_create_pin_404_item(client, auth_headers, pins, exception):
    config = {
        'item_id': mock.to_uuid(404, 'item'),
    }
    mock.last_uuid = mock.OFFSETS['pin'] + len(pins)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items/pins", headers=auth_headers(1), json=config)
    assert response.json() == exception("entity_not_found", f"Unable to find item with id={mock.to_uuid(404, 'item')}")
    assert response.status_code == 404

def test_create_pin_duplicate(client, auth_headers, pins, exception):
    config = {
        'item_id': mock.to_uuid(2, 'item'),
    }
    mock.last_uuid = mock.OFFSETS['pin'] + len(pins)
    response = client.post(f"/boards/{mock.to_uuid(2, 'board')}/items/pins", headers=auth_headers(1), json=config)
    assert response.json() == exception("duplicate_entity", f"Entity pin with item_id={mock.to_uuid(2, 'item')} already exists")
    assert response.status_code == 422

def test_update_pin(client, auth_headers, get_pin):
    update = { 'label': 'Updated' } # this pin has compass set to True which is good for testing since compass is set to false by default
    expected = get_pin(1)
    expected['label'] = 'Updated'
    response = client.put(f"/boards/{mock.to_uuid(2, 'board')}/items/pins/{mock.to_uuid(1, 'pin')}", headers=auth_headers(1), json=update)
    assert response.json() == expected
    assert response.status_code == 200

def test_update_404_pin(client, auth_headers, exception):
    update = { 'label': 'Updated' } # this pin has compass set to True which is good for testing since compass is set to false by default
    response = client.put(f"/boards/{mock.to_uuid(2, 'board')}/items/pins/{mock.to_uuid(404, 'pin')}", headers=auth_headers(1), json=update)
    assert response.json() == exception('entity_not_found', f"Unable to find pin with id={mock.to_uuid(404, 'pin')}")
    assert response.status_code == 404

def test_update_pin_move(client, auth_headers, get_pin, get_item):
    update = { 'item_id': mock.to_uuid(6, 'item') } # this pin is on list 1 and connected to the one on list 2, we move to the todo list
    expected = get_pin(1)
    expected['item_id'] = mock.to_uuid(6, 'item')
    response = client.put(f"/boards/{mock.to_uuid(2, 'board')}/items/pins/{mock.to_uuid(1, 'pin')}", headers=auth_headers(1), json=update)
    assert response.json() == expected
    assert response.status_code == 200
    # Make sure the relevant items are updated
    expected = get_item(2)
    pin, expected['pin'] = expected['pin'], None
    response = client.get(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(2, 'item')}")
    assert response.json() == expected
    assert response.status_code == 200
    expected = get_item(6)
    pin['item_id'] = mock.to_uuid(6, 'item')
    expected['pin'] = pin
    response = client.get(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(6, 'item')}")
    assert response.json() == expected
    assert response.status_code == 200

def test_update_pin_move_404(client, auth_headers, exception, get_item):
    update = { 'item_id': mock.to_uuid(404, 'item') }
    response = client.put(f"/boards/{mock.to_uuid(2, 'board')}/items/pins/{mock.to_uuid(1, 'pin')}", headers=auth_headers(1), json=update)
    assert response.json() == exception("entity_not_found", f"Unable to find item with id={mock.to_uuid(404, 'item')}")
    assert response.status_code == 404
    # Make sure the item still has the pin
    response = client.get(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(2, 'item')}")
    assert response.json() == get_item(2)
    assert response.status_code == 200

def test_update_pin_move_duplicate(client, auth_headers, exception, get_item):
    update = { 'item_id': mock.to_uuid(11, 'item') } # move to Board 2 Item which already has a pin
    response = client.put(f"/boards/{mock.to_uuid(2, 'board')}/items/pins/{mock.to_uuid(1, 'pin')}", headers=auth_headers(1), json=update)
    assert response.json() == exception("duplicate_entity", f"Entity pin with item_id={mock.to_uuid(11, 'item')} already exists")
    assert response.status_code == 422
    # Make sure the relevant items are unchanged
    response = client.get(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(2, 'item')}")
    assert response.json() == get_item(2)
    assert response.status_code == 200
    response = client.get(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(11, 'item')}")
    assert response.json() == get_item(11)
    assert response.status_code == 200

def test_update_pin_move_between_boards(client, auth_headers, exception, get_item):
    update = { 'item_id': mock.to_uuid(1, 'item') } # move to item 1 which is on board 1
    response = client.put(f"/boards/{mock.to_uuid(2, 'board')}/items/pins/{mock.to_uuid(1, 'pin')}", headers=auth_headers(1), json=update)
    assert response.json() == exception("entity_not_found", f"Unable to find item with id={mock.to_uuid(1, 'item')}")
    assert response.status_code == 404
    # Make sure the relevant items are unchanged
    response = client.get(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(2, 'item')}")
    assert response.json() == get_item(2)
    assert response.status_code == 200
    response = client.get(f"/boards/{mock.to_uuid(1, 'board')}/items/{mock.to_uuid(1, 'item')}")
    assert response.json() == get_item(1)
    assert response.status_code == 200

def test_delete_pin(client, auth_headers, get_item):
    response = client.delete(f"/boards/{mock.to_uuid(2, 'board')}/items/pins/{mock.to_uuid(3, 'pin')}", headers=auth_headers(1))
    assert response.status_code == 204
    # Make sure it's gone
    expected = get_item(11)
    expected['pin'] = None
    response = client.get(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(11, 'item')}")
    assert response.json() == expected
    assert response.status_code == 200

def test_delete_pin_with_connection(client, auth_headers, get_item):
    response = client.delete(f"/boards/{mock.to_uuid(2, 'board')}/items/pins/{mock.to_uuid(1, 'pin')}", headers=auth_headers(1))
    assert response.status_code == 204
    # Make sure it's gone, and the other pin doesn't have a connection
    expected = get_item(2)
    expected['pin'] = None
    response = client.get(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(2, 'item')}")
    assert response.json() == expected
    assert response.status_code == 200
    expected = get_item(9)
    expected['pin']['connections'].remove(mock.to_uuid(1, 'pin'))
    response = client.get(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(9, 'item')}")
    assert response.json() == expected
    assert response.status_code == 200

def test_delete_404_pin(client, auth_headers, exception):
    response = client.delete(f"/boards/{mock.to_uuid(2, 'board')}/items/pins/{mock.to_uuid(404, 'pin')}", headers=auth_headers(1))
    assert response.json() == exception("entity_not_found", f"Unable to find pin with id={mock.to_uuid(404, 'pin')}")
    assert response.status_code == 404

def test_add_connection(client, auth_headers, get_pin):
    response = client.put(f"/boards/{mock.to_uuid(2, 'board')}/items/pins/connect?p1={mock.to_uuid(1, 'pin')}&p2={mock.to_uuid(3, 'pin')}", headers=auth_headers(1))
    p1, p3 = get_pin(1), get_pin(3)
    p1['connections'].append(mock.to_uuid(3, 'pin'))
    p3['connections'].append(mock.to_uuid(1, 'pin'))
    assert response.json() == [ p1, p3 ]
    assert response.status_code == 200

def test_remove_connection(client, auth_headers, get_pin):
    response = client.delete(f"/boards/{mock.to_uuid(2, 'board')}/items/pins/connect?p1={mock.to_uuid(1, 'pin')}&p2={mock.to_uuid(2, 'pin')}", headers=auth_headers(1))
    p1, p2 = get_pin(1), get_pin(2)
    p1['connections'].remove(mock.to_uuid(2, 'pin'))
    p2['connections'].remove(mock.to_uuid(1, 'pin'))
    assert response.json() == [ p1, p2 ]
    assert response.status_code == 200

def test_add_connection_reversed(client, auth_headers, get_pin):
    response = client.put(f"/boards/{mock.to_uuid(2, 'board')}/items/pins/connect?p1={mock.to_uuid(3, 'pin')}&p2={mock.to_uuid(1, 'pin')}", headers=auth_headers(1))
    p1, p3 = get_pin(1), get_pin(3)
    p1['connections'].append(mock.to_uuid(3, 'pin'))
    p3['connections'].append(mock.to_uuid(1, 'pin'))
    assert response.json() == [ p3, p1 ]
    assert response.status_code == 200

def test_remove_connection_reversed(client, auth_headers, get_pin):
    response = client.delete(f"/boards/{mock.to_uuid(2, 'board')}/items/pins/connect?p1={mock.to_uuid(2, 'pin')}&p2={mock.to_uuid(1, 'pin')}", headers=auth_headers(1))
    p1, p2 = get_pin(1), get_pin(2)
    p1['connections'].remove(mock.to_uuid(2, 'pin'))
    p2['connections'].remove(mock.to_uuid(1, 'pin'))
    assert response.json() == [ p2, p1 ]
    assert response.status_code == 200

def test_add_connection_existing_unchanged(client, auth_headers, get_pin):
    response = client.put(f"/boards/{mock.to_uuid(2, 'board')}/items/pins/connect?p1={mock.to_uuid(1, 'pin')}&p2={mock.to_uuid(2, 'pin')}", headers=auth_headers(1))
    assert response.json() == [ get_pin(1), get_pin(2) ]
    assert response.status_code == 200

def test_remove_connection_nonexisting_unchanged(client, auth_headers, get_pin):
    response = client.delete(f"/boards/{mock.to_uuid(2, 'board')}/items/pins/connect?p1={mock.to_uuid(1, 'pin')}&p2={mock.to_uuid(3, 'pin')}", headers=auth_headers(1))
    assert response.json() == [ get_pin(1), get_pin(3) ]
    assert response.status_code == 200

def test_add_connection_wrong_board(client, auth_headers, exception):
    response = client.put(f"/boards/{mock.to_uuid(1, 'board')}/items/pins/connect?p1={mock.to_uuid(1, 'pin')}&p2={mock.to_uuid(3, 'pin')}", headers=auth_headers(1))
    assert response.json() == exception('entity_not_found', f"Unable to find pin with id={mock.to_uuid(1, 'pin')}")
    assert response.status_code == 404

def test_add_connection_from_404(client, auth_headers, exception):
    response = client.put(f"/boards/{mock.to_uuid(2, 'board')}/items/pins/connect?p1={mock.to_uuid(404, 'pin')}&p2={mock.to_uuid(3, 'pin')}", headers=auth_headers(1))
    assert response.json() == exception('entity_not_found', f"Unable to find pin with id={mock.to_uuid(404, 'pin')}")
    assert response.status_code == 404

def test_add_connection_to_404(client, auth_headers, exception):
    response = client.put(f"/boards/{mock.to_uuid(2, 'board')}/items/pins/connect?p1={mock.to_uuid(1, 'pin')}&p2={mock.to_uuid(404, 'pin')}", headers=auth_headers(1))
    assert response.json() == exception('entity_not_found', f"Unable to find pin with id={mock.to_uuid(404, 'pin')}")
    assert response.status_code == 404

def test_remove_connection_wrong_board(client, auth_headers, exception):
    response = client.delete(f"/boards/{mock.to_uuid(1, 'board')}/items/pins/connect?p1={mock.to_uuid(1, 'pin')}&p2={mock.to_uuid(2, 'pin')}", headers=auth_headers(1))
    assert response.json() == exception('entity_not_found', f"Unable to find pin with id={mock.to_uuid(1, 'pin')}")
    assert response.status_code == 404

def test_remove_connection_from_404(client, auth_headers, exception):
    response = client.delete(f"/boards/{mock.to_uuid(2, 'board')}/items/pins/connect?p1={mock.to_uuid(404, 'pin')}&p2={mock.to_uuid(2, 'pin')}", headers=auth_headers(1))
    assert response.json() == exception('entity_not_found', f"Unable to find pin with id={mock.to_uuid(404, 'pin')}")
    assert response.status_code == 404

def test_remove_connection_to_404(client, auth_headers, exception):
    response = client.delete(f"/boards/{mock.to_uuid(2, 'board')}/items/pins/connect?p1={mock.to_uuid(1, 'pin')}&p2={mock.to_uuid(404, 'pin')}", headers=auth_headers(1))
    assert response.json() == exception('entity_not_found', f"Unable to find pin with id={mock.to_uuid(404, 'pin')}")
    assert response.status_code == 404

def test_add_pin_unauthorized(client, auth_headers, exception):
    response = client.post(f"/boards/{mock.to_uuid(3, 'board')}/items/pins", headers=auth_headers(4), json={ 'item_id': mock.to_uuid(8, 'item') })
    assert response.json() == exception('entity_not_found', f"Unable to find board with id={mock.to_uuid(3, 'board')}")
    assert response.status_code == 404

def test_add_connection_unauthorized(client, auth_headers, exception):
    response = client.put(f"/boards/{mock.to_uuid(2, 'board')}/items/pins/connect?p1={mock.to_uuid(1, 'pin')}&p2={mock.to_uuid(3, 'pin')}", headers=auth_headers(4))
    assert response.json() == exception("access_denied", "Access denied")
    assert response.status_code == 403