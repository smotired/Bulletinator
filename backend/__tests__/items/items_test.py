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

def test_create_item_default_values(client, auth_headers, def_item):
    item = {
        "type": "note",
        "text": "Created Note",
    }
    response = client.post("/boards/1/items", headers=auth_headers(1), json=item)
    assert response.json() == {
        **def_item(1),
        **item,
        "size": "300,200",
    }
    assert response.status_code == 201

def test_create_private_item(client, auth_headers, def_item):
    item = {
        "type": "note",
        "text": "Private Note",
    }
    response = client.post("/boards/3/items", headers=auth_headers(3), json=item)
    assert response.json() == {
        **def_item(3),
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

def test_create_link(client, auth_headers, def_item):
    item = {
        "type": "link",
        "title": "Created Link",
        "url": "/boards/2",
    }
    response = client.post("/boards/1/items", headers=auth_headers(1), json=item)
    assert response.json() == {
        **def_item(1),
        **item,
    }
    assert response.status_code == 201

def test_create_link_default(client, auth_headers, def_item):
    """Link has no optional fields but this is here in case we add some later"""
    item = {
        "type": "link",
        "title": "Created Link",
        "url": "/boards/2",
    }
    response = client.post("/boards/1/items", headers=auth_headers(1), json=item)
    assert response.json() == {
        **def_item(1),
        **item,
    }
    assert response.status_code == 201

def test_create_link_missing(client, auth_headers, exception):
    item = { "type": "link" }
    response = client.post("/boards/1/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("missing_item_fields", "Item type 'link' was missing the following fields: title, url")
    assert response.status_code == 422

# Add tests for creating media once item uploading is implemented.

def test_create_todo(client, auth_headers, def_item, empty_collection):
    item = {
        "type": "todo",
        "title": "Created Todo",
    }
    response = client.post("/boards/1/items", headers=auth_headers(1), json=item)
    assert response.json() == {
        **def_item(1),
        **item,
        "contents": empty_collection("items")
    }
    assert response.status_code == 201

def test_create_todo_default(client, auth_headers, def_item, empty_collection):
    """Todo has no optional fields but this is here in case we add some later"""
    item = {
        "type": "todo",
        "title": "Created Todo",
    }
    response = client.post("/boards/1/items", headers=auth_headers(1), json=item)
    assert response.json() == {
        **def_item(1),
        **item,
        "contents": empty_collection("items")
    }
    assert response.status_code == 201

def test_create_todo_missing(client, auth_headers, exception):
    item = { "type": "todo" }
    response = client.post("/boards/1/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("missing_item_fields", "Item type 'todo' was missing the following fields: title")
    assert response.status_code == 422

def test_create_list(client, auth_headers, def_item, empty_collection):
    item = {
        "type": "list",
        "title": "Created Todo",
    }
    response = client.post("/boards/1/items", headers=auth_headers(1), json=item)
    assert response.json() == {
        **def_item(1),
        **item,
        "contents": empty_collection("items")
    }
    assert response.status_code == 201

def test_create_list_default(client, auth_headers, def_item, empty_collection):
    """List has no optional fields but this is here in case we add some later"""
    item = {
        "type": "list",
        "title": "Created List",
    }
    response = client.post("/boards/1/items", headers=auth_headers(1), json=item)
    assert response.json() == {
        **def_item(1),
        **item,
        "contents": empty_collection("items")
    }
    assert response.status_code == 201

def test_create_list_missing(client, auth_headers, exception):
    item = { "type": "list" }
    response = client.post("/boards/1/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("missing_item_fields", "Item type 'list' was missing the following fields: title")
    assert response.status_code == 422

def test_append_to_list(client, auth_headers, get_item):
    # Add an item to the end of a list
    item = {
        "list_id": 2,
        "type": "note",
        "text": "Appended Note"
    }
    updated_item = {
        **item,
        "id": 9,
        "board_id": 2,
        "position": None,
        "index": 2, # there are 2 items in the list already
        "size": "300,200"
    }
    response = client.post("/boards/2/items", headers=auth_headers(1), json=item)
    assert response.json() == updated_item
    assert response.status_code == 201
    # Try getting the list to make sure it's in there
    response = client.get("/boards/2/items/2")
    list_item = get_item(2)
    list_item['contents']['metadata']['count'] = 3
    list_item['contents']['items'].append(updated_item)
    assert response.json() == list_item
    assert response.status_code == 200

def test_insert_into_list(client, auth_headers, get_item):
    # Insert an item into the middle of a list
    item = {
        "list_id": 2,
        "type": "note",
        "text": "Inserted Note",
        "index": 1,
    }
    updated_item = {
        **item,
        "id": 9,
        "board_id": 2,
        "position": None,
        "size": "300,200"
    }
    response = client.post("/boards/2/items", headers=auth_headers(1), json=item)
    assert response.json() == updated_item
    assert response.status_code == 201
    # Try getting the list to make sure it's in there
    response = client.get("/boards/2/items/2")
    list_item = get_item(2)
    list_item['contents']['metadata']['count'] = 3
    list_item['contents']['items'][1]['index'] = 2
    list_item['contents']['items'].insert(1, updated_item)
    assert response.json() == list_item
    assert response.status_code == 200

def test_insert_at_end(client, auth_headers, get_item):
    item = {
        "list_id": 2,
        "type": "note",
        "text": "Inserted Note",
        "index": 2,
    }
    updated_item = {
        **item,
        "id": 9,
        "board_id": 2,
        "position": None,
        "size": "300,200"
    }
    response = client.post("/boards/2/items", headers=auth_headers(1), json=item)
    assert response.json() == updated_item
    assert response.status_code == 201
    response = client.get("/boards/2/items/2")
    list_item = get_item(2)
    list_item['contents']['metadata']['count'] = 3
    list_item['contents']['items'].append(updated_item)
    assert response.json() == list_item
    assert response.status_code == 200

def test_append_to_404_list(client, auth_headers, exception):
    item = {
        "list_id": 404,
        "type": "note",
        "text": "Appended Note"
    }
    response = client.post("/boards/1/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("entity_not_found", "Unable to find item_list with id=404")
    assert response.status_code == 404

def test_append_to_external_list(client, auth_headers, exception):
    item = {
        "list_id": 2,
        "type": "note",
        "text": "Appended Note"
    }
    response = client.post("/boards/1/items", headers=auth_headers(1), json=item) # the list with id 2 is on board 1
    assert response.json() == exception("entity_not_found", "Unable to find item_list with id=2")
    assert response.status_code == 404

def test_append_to_non_list(client, auth_headers, exception):
    item = {
        "list_id": 1,
        "type": "note",
        "text": "Appended Note"
    }
    response = client.post("/boards/1/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("item_type_mismatch", "Item with id=1 has type 'note', but was treated as if it had type 'list'")
    assert response.status_code == 418

def test_insert_out_of_range_l(client, auth_headers, exception):
    item = {
        "list_id": 2,
        "type": "note",
        "text": "Inserted Note",
        "index": 3,
    }
    response = client.post("/boards/2/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("out_of_range", "Index 3 out of range for item_list with id=2")
    assert response.status_code == 422

def test_insert_out_of_range_s(client, auth_headers, exception):
    item = {
        "list_id": 2,
        "type": "note",
        "text": "Inserted Note",
        "index": -1,
    }
    response = client.post("/boards/2/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("out_of_range", "Index -1 out of range for item_list with id=2")
    assert response.status_code == 422

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