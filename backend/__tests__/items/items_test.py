"""Module for testing the item routes"""

from backend.__tests__ import mock

def test_get_items1(client, get_item):
    response = client.get(f"/boards/{mock.to_uuid(1, 'board')}/items")
    assert response.json() == {
        "metadata": { "count": 3 },
        "items": [ get_item(1), get_item(5), get_item(7) ]
    }
    assert response.status_code == 200

def test_get_items2(client, get_item):
    response = client.get(f"/boards/{mock.to_uuid(2, 'board')}/items")
    assert response.json() == {
        "metadata": { "count": 4 },
        "items": [ get_item(2), get_item(6), get_item(9), get_item(11) ]
    }
    assert response.status_code == 200

def test_get_private_items(client, auth_headers, get_item):
    response = client.get(f"/boards/{mock.to_uuid(3, 'board')}/items", headers=auth_headers(3))
    assert response.json() == {
        "metadata": { "count": 1 },
        "items": [ get_item(8) ]
    }
    assert response.status_code == 200

def test_get_private_items_unauthorized(client, auth_headers, exception):
    response = client.get(f"/boards/{mock.to_uuid(3, 'board')}/items", headers=auth_headers(4)) # account 4 should have no knowledge of board 3
    assert response.json() == exception("entity_not_found", f"Unable to find board with id={mock.to_uuid(3, 'board')}")
    assert response.status_code == 404

def test_get_item(client, get_item):
    response = client.get(f"/boards/{mock.to_uuid(1, 'board')}/items/{mock.to_uuid(1, 'item')}")
    assert response.json() == get_item(1)
    assert response.status_code == 200

def test_get_404_item(client, exception):
    response = client.get(f"/boards/{mock.to_uuid(1, 'board')}/items/{mock.to_uuid(404, 'item')}")
    assert response.json() == exception("entity_not_found", f"Unable to find item with id={mock.to_uuid(404, 'item')}")
    assert response.status_code == 404

def test_get_private_item(client, auth_headers, get_item):
    response = client.get(f"/boards/{mock.to_uuid(3, 'board')}/items/{mock.to_uuid(8, 'item')}", headers=auth_headers(3))
    assert response.json() == get_item(8)
    assert response.status_code == 200

def test_get_private_item_unauthorized(client, auth_headers, exception):
    response = client.get(f"/boards/{mock.to_uuid(3, 'board')}/items/{mock.to_uuid(8, 'item')}", headers=auth_headers(4))
    assert response.json() == exception("entity_not_found", f"Unable to find board with id={mock.to_uuid(3, 'board')}")
    assert response.status_code == 404

def test_get_item_on_different_board(client, exception):
    response = client.get(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(1, 'item')}")
    assert response.json() == exception("entity_not_found", f"Unable to find item with id={mock.to_uuid(1, 'item')}")
    assert response.status_code == 404

def test_get_item_link(client, get_item):
    response = client.get(f"/boards/{mock.to_uuid(1, 'board')}/items/{mock.to_uuid(1, 'item')}")
    assert response.json() == get_item(1)
    assert response.status_code == 200

def test_get_item_todo(client, get_item):
    response = client.get(f"/boards/{mock.to_uuid(1, 'board')}/items/{mock.to_uuid(5, 'item')}")
    assert response.json() == get_item(5)
    assert response.status_code == 200

def test_get_item_list(client, get_item):
    response = client.get(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(2, 'item')}")
    assert response.json() == get_item(2)
    assert response.status_code == 200

def test_create_item(client, auth_headers, items, get_item):
    item = {
        "list_id": None,
        "position": "200,200",
        "index": None,
        "type": "note",
        "text": "Created Note",
    }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    updated_item = {
        "id": mock.to_uuid(len(items) + 1, 'item'),
        "board_id": mock.to_uuid(1, 'board'),
        "pin": None,
        **item,
    }
    assert response.json() == updated_item
    assert response.status_code == 201
    response = client.get(f"/boards/{mock.to_uuid(1, 'board')}/items")
    assert response.json() == {
        "metadata": { "count": 4 },
        "items": [ get_item(1), get_item(5), get_item(7), updated_item ]
    }
    assert response.status_code == 200

def test_create_item_as_viewer(client, auth_headers, items, exception):
    item = {
        "list_id": None,
        "position": "200,200",
        "index": None,
        "type": "note",
        "text": "Created Note",
    }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(3), json=item)
    assert response.json() == exception("no_permissions", f"No permissions to modify board on board with id={mock.to_uuid(1, 'board')}")
    assert response.status_code == 403

def test_create_invalid_item(client, auth_headers, items, exception):
    item = { "type": "foo" }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("invalid_item_type", "Item type 'foo' is not valid")
    assert response.status_code == 422

def test_create_item_default_values(client, auth_headers, items, def_item):
    item = {
        "type": "note",
        "text": "Created Note",
    }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == {
        **def_item(1),
        **item,
    }
    assert response.status_code == 201

def test_create_private_item(client, auth_headers, items, def_item):
    item = {
        "type": "note",
        "text": "Private Note",
    }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(3, 'board')}/items", headers=auth_headers(3), json=item)
    assert response.json() == {
        **def_item(3),
        **item,
    }
    assert response.status_code == 201


def test_create_private_item_unauthorized(client, auth_headers, items, exception):
    item = {
        "type": "note",
        "text": "Illegal Note",
    }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(3, 'board')}/items", headers=auth_headers(4), json=item)
    assert response.json() == exception("entity_not_found", f"Unable to find board with id={mock.to_uuid(3, 'board')}")
    assert response.status_code == 404

def test_create_item_missing_fields(client, auth_headers, items, exception):
    item = { "type": "note" }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("missing_item_fields", "Item type 'note' was missing the following fields: text")
    assert response.status_code == 422

def test_create_note_too_long(client, auth_headers, items, exception):
    item = { "type": "note", "text": "a"*301 }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("field_too_long", "Input to field 'text' exceeded the maximum length")
    assert response.status_code == 422

def test_create_link(client, auth_headers, items, def_item):
    item = {
        "type": "link",
        "title": "Created Link",
        "url": f"/boards/{mock.to_uuid(2, 'board')}",
    }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == {
        **def_item(1),
        **item,
    }
    assert response.status_code == 201

def test_create_link_default(client, auth_headers, items, def_item):
    """Link has no optional fields but this is here in case we add some later"""
    item = {
        "type": "link",
        "title": "Created Link",
        "url": f"/boards/{mock.to_uuid(2, 'board')}",
    }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == {
        **def_item(1),
        **item,
    }
    assert response.status_code == 201

def test_create_link_missing(client, auth_headers, items, exception):
    item = { "type": "link" }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("missing_item_fields", "Item type 'link' was missing the following fields: title, url")
    assert response.status_code == 422

def test_create_link_title_too_long(client, auth_headers, items, exception):
    item = { "type": "link", "title": "a"*129, "url": "/" }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("field_too_long", "Input to field 'title' exceeded the maximum length")
    assert response.status_code == 422

def test_create_link_url_too_long(client, auth_headers, items, exception):
    item = { "type": "link", "title": "Link", "url": "a"*129 }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("field_too_long", "Input to field 'url' exceeded the maximum length")
    assert response.status_code == 422

def test_create_media_image(client, auth_headers, items, def_item):
    item = {
        "type": "media",
        "url": "/static/images/test_image.png",
        "size": "600,400",
    }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == {
        **def_item(1),
        **item,
    }
    assert response.status_code == 201

def test_create_media_url_too_long(client, auth_headers, items, exception):
    item = { "type": "media", "url": "a"*129 }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("field_too_long", "Input to field 'url' exceeded the maximum length")
    assert response.status_code == 422

def test_create_media_invalid_size1(client, auth_headers, items, exception):
    item = { "type": "media", "url": "/", "size": "invalid" }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("invalid_field", f"Value '{item['size']}' is invalid for field 'size'")
    assert response.status_code == 422

def test_create_media_invalid_size2(client, auth_headers, items, exception):
    item = { "type": "media", "url": "/", "size": "fifty,onehunderd" }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("invalid_field", f"Value '{item['size']}' is invalid for field 'size'")
    assert response.status_code == 422

def test_create_media_invalid_size3(client, auth_headers, items, exception):
    item = { "type": "media", "url": "/", "size": "235.2,643.5" }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("invalid_field", f"Value '{item['size']}' is invalid for field 'size'")
    assert response.status_code == 422

def test_create_media_invalid_size4(client, auth_headers, items, exception):
    item = { "type": "media", "url": "/", "size": "100,200,300" }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("invalid_field", f"Value '{item['size']}' is invalid for field 'size'")
    assert response.status_code == 422

def test_create_media_invalid_size5(client, auth_headers, items, exception):
    item = { "type": "media", "url": "/", "size": "600" }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("invalid_field", f"Value '{item['size']}' is invalid for field 'size'")
    assert response.status_code == 422

def test_create_media_invalid_size6(client, auth_headers, items, exception):
    item = { "type": "media", "url": "/", "size": "2001,2001" }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("invalid_field", f"Value '{item['size']}' is invalid for field 'size'")
    assert response.status_code == 422

def test_create_media_image_default(client, auth_headers, items, def_item):
    item = {
        "type": "media",
        "url": "/static/images/test_image.png",
    }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == {
        **def_item(1),
        **item,
        "size": None, # default to just the image size
    }
    assert response.status_code == 201

def test_create_media_image_missing(client, auth_headers, items, exception):
    item = { "type": "media" }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("missing_item_fields", "Item type 'media' was missing the following fields: url")
    assert response.status_code == 422

def test_create_todo(client, auth_headers, def_item, items, empty_collection):
    item = {
        "type": "todo",
        "title": "Created Todo",
    }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == {
        **def_item(1),
        **item,
        "contents": empty_collection("items")
    }
    assert response.status_code == 201

def test_create_todo_title_too_long(client, auth_headers, items, exception):
    item = { "type": "todo", "title": "a"*65 }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("field_too_long", "Input to field 'title' exceeded the maximum length")
    assert response.status_code == 422

def test_create_todo_default(client, auth_headers, def_item, items, empty_collection):
    """Todo has no optional fields but this is here in case we add some later"""
    item = {
        "type": "todo",
        "title": "Created Todo",
    }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == {
        **def_item(1),
        **item,
        "contents": empty_collection("items")
    }
    assert response.status_code == 201

def test_create_todo_missing(client, auth_headers, items, exception):
    item = { "type": "todo" }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("missing_item_fields", "Item type 'todo' was missing the following fields: title")
    assert response.status_code == 422

def test_create_list(client, auth_headers, def_item, items, empty_collection):
    item = {
        "type": "list",
        "title": "Created Todo",
    }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == {
        **def_item(1),
        **item,
        "contents": empty_collection("items")
    }
    assert response.status_code == 201

def test_create_list_default(client, auth_headers, items, def_item, empty_collection):
    """List has no optional fields but this is here in case we add some later"""
    item = {
        "type": "list",
        "title": "Created List",
    }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == {
        **def_item(1),
        **item,
        "contents": empty_collection("items")
    }
    assert response.status_code == 201

def test_create_list_missing(client, items, auth_headers, exception):
    item = { "type": "list" }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("missing_item_fields", "Item type 'list' was missing the following fields: title")
    assert response.status_code == 422

def test_create_list_title_too_long(client, auth_headers, items, exception):
    item = { "type": "list", "title": "a"*65 }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("field_too_long", "Input to field 'title' exceeded the maximum length")
    assert response.status_code == 422

def test_create_document(client, auth_headers, items, def_item):
    item = {
        "type": "document",
        "title": "Created Document",
        "text": "Text in a _document_ can be formatted *richly*.",
    }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == {
        **def_item(1),
        **item,
    }
    assert response.status_code == 201

def test_create_document_default(client, auth_headers, items, def_item):
    """Document has no optional fields but this is here in case we add some later"""
    item = {
        "type": "document",
        "title": "Created Document",
    }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == {
        **def_item(1),
        **item,
        "text": "",
    }
    assert response.status_code == 201

def test_create_document_missing(client, auth_headers, items, exception):
    item = { "type": "document" }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("missing_item_fields", "Item type 'document' was missing the following fields: title")
    assert response.status_code == 422

def test_create_document_title_too_long(client, auth_headers, items, exception):
    item = { "type": "todo", "title": "a"*65 }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("field_too_long", "Input to field 'title' exceeded the maximum length")
    assert response.status_code == 422

def test_create_append_to_list(client, auth_headers, items, get_item):
    # Add an item to the end of a list
    item = {
        "list_id": mock.to_uuid(2, 'item'),
        "type": "note",
        "text": "Appended Note"
    }
    updated_item = {
        **item,
        "id": mock.to_uuid(len(items) + 1, 'item'),
        "board_id": mock.to_uuid(2, 'board'),
        "position": None,
        "index": 2, # there are 2 items in the list already
        "pin": None,
    }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(2, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == updated_item
    assert response.status_code == 201
    # Try getting the list to make sure it's in there
    response = client.get(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(2, 'item')}")
    list_item = get_item(2)
    list_item['contents']['metadata']['count'] = 3
    list_item['contents']['items'].append(updated_item)
    assert response.json() == list_item
    assert response.status_code == 200

def test_create_insert_into_list(client, auth_headers, items, get_item):
    # Insert an item into the middle of a list
    item = {
        "list_id": mock.to_uuid(2, 'item'),
        "type": "note",
        "text": "Inserted Note",
        "index": 1,
    }
    updated_item = {
        **item,
        "id": mock.to_uuid(len(items) + 1, 'item'),
        "board_id": mock.to_uuid(2, 'board'),
        "position": None,
        "pin": None,
    }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(2, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == updated_item
    assert response.status_code == 201
    # Try getting the list to make sure it's in there
    response = client.get(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(2, 'item')}")
    list_item = get_item(2)
    list_item['contents']['metadata']['count'] = 3
    list_item['contents']['items'][1]['index'] = 2
    list_item['contents']['items'].insert(1, updated_item)
    assert response.json() == list_item
    assert response.status_code == 200

def test_create_insert_at_end(client, auth_headers, items, get_item):
    item = {
        "list_id": mock.to_uuid(2, 'item'),
        "type": "note",
        "text": "Inserted Note",
        "index": 2,
    }
    updated_item = {
        **item,
        "id": mock.to_uuid(len(items) + 1, 'item'),
        "board_id": mock.to_uuid(2, 'board'),
        "position": None,
        "pin": None,
    }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(2, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == updated_item
    assert response.status_code == 201
    response = client.get(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(2, 'item')}")
    list_item = get_item(2)
    list_item['contents']['metadata']['count'] = 3
    list_item['contents']['items'].append(updated_item)
    assert response.json() == list_item
    assert response.status_code == 200

def test_append_to_404_list(client, auth_headers, exception):
    item = {
        "list_id": mock.to_uuid(404, 'item'),
        "type": "note",
        "text": "Appended Note"
    }
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("entity_not_found", f"Unable to find item_list with id={mock.to_uuid(404, 'item')}")
    assert response.status_code == 404

def test_append_to_external_list(client, auth_headers, exception):
    item = {
        "list_id": mock.to_uuid(2, 'item'),
        "type": "note",
        "text": "Appended Note"
    }
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item) # the list with id 2 is on board 1
    assert response.json() == exception("entity_not_found", f"Unable to find item_list with id={mock.to_uuid(2, 'item')}")
    assert response.status_code == 404

def test_append_to_non_list(client, auth_headers, exception):
    item = {
        "list_id": mock.to_uuid(1, 'item'),
        "type": "note",
        "text": "Appended Note"
    }
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("item_type_mismatch", f"Item with id={mock.to_uuid(1, 'item')} has type 'note', but was treated as if it had type 'list'")
    assert response.status_code == 418

def test_insert_out_of_range_l(client, auth_headers, exception):
    item = {
        "list_id": mock.to_uuid(2, 'item'),
        "type": "note",
        "text": "Inserted Note",
        "index": 3,
    }
    response = client.post(f"/boards/{mock.to_uuid(2, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("out_of_range", f"Index 3 out of range for item_list with id={mock.to_uuid(2, 'item')}")
    assert response.status_code == 422

def test_insert_out_of_range_s(client, auth_headers, exception):
    item = {
        "list_id": mock.to_uuid(2, 'item'),
        "type": "note",
        "text": "Inserted Note",
        "index": -1,
    }
    response = client.post(f"/boards/{mock.to_uuid(2, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == exception("out_of_range", f"Index -1 out of range for item_list with id={mock.to_uuid(2, 'item')}")
    assert response.status_code == 422

def test_add_list_to_list(client, auth_headers, exception):
    # Add a list to another list
    item = {
        "list_id": mock.to_uuid(2, 'item'),
        "type": "list",
        "title": "Double List"
    }
    response = client.post(f"/boards/{mock.to_uuid(2, 'board')}/items", headers=auth_headers(1), json=item)
    assert response.json() == exception('add_list_to_list', 'Cannot add a list to another list')
    assert response.status_code == 422

def test_update_item(client, auth_headers, get_item):
    update = { "text": "Updated" }
    updated = get_item(1)
    updated['text'] = "Updated"
    response = client.put(f"/boards/{mock.to_uuid(1, 'board')}/items/{mock.to_uuid(1, 'item')}", headers=auth_headers(1), json=update)
    assert response.json() == updated
    assert response.status_code == 200

def test_update_404_item(client, auth_headers, exception):
    update = { "text": "Updated" }
    response = client.put(f"/boards/{mock.to_uuid(1, 'board')}/items/{mock.to_uuid(404, 'item')}", headers=auth_headers(1), json=update)
    assert response.json() == exception('entity_not_found', f'Unable to find item with id={mock.to_uuid(404, 'item')}')
    assert response.status_code == 404

def test_update_item_unauthorized(client, auth_headers, exception):
    update = { "text": "Updated" }
    response = client.put(f"/boards/{mock.to_uuid(3, 'board')}/items/{mock.to_uuid(8, 'item')}", headers=auth_headers(4), json=update)
    assert response.json() == exception('entity_not_found', f'Unable to find board with id={mock.to_uuid(3, 'board')}')
    assert response.status_code == 404

def test_update_item_wrong_board(client, auth_headers, exception):
    update = { "text": "Updated" }
    response = client.put(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(1, 'item')}", headers=auth_headers(1), json=update)
    assert response.json() == exception('entity_not_found', f'Unable to find item with id={mock.to_uuid(1, 'item')}')
    assert response.status_code == 404

def test_update_add_to_list(client, auth_headers, get_item):
    update = { "list_id": mock.to_uuid(2, 'item') }
    updated = get_item(11)
    updated['position'] = None
    updated['list_id'] = mock.to_uuid(2, 'item')
    updated['index'] = 2
    response = client.put(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(11, 'item')}", headers=auth_headers(1), json=update)
    assert response.json() == updated
    assert response.status_code == 200
    # make sure it's in the list
    response = client.get(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(2, 'item')}")
    list_item = get_item(2)
    list_item['contents']['metadata']['count'] = 3
    list_item['contents']['items'].append(updated)
    assert response.json() == list_item
    assert response.status_code == 200

def test_update_insert_to_list(client, auth_headers, get_item):
    update = { "list_id": mock.to_uuid(2, 'item'), "index": 1 }
    updated = get_item(11)
    updated['position'] = None
    updated['list_id'] = mock.to_uuid(2, 'item')
    updated['index'] = 1
    response = client.put(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(11, 'item')}", headers=auth_headers(1), json=update)
    assert response.json() == updated
    assert response.status_code == 200
    # make sure it's in the list
    response = client.get(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(2, 'item')}")
    list_item = get_item(2)
    list_item['contents']['metadata']['count'] = 3
    list_item['contents']['items'].insert(1, updated)
    list_item['contents']['items'][2]['index'] = 2
    assert response.json() == list_item
    assert response.status_code == 200

def test_update_remove_from_list(client, auth_headers, get_item):
    update = { "position": "700,0" }
    updated = get_item(4)
    updated['position'] = "700,0"
    updated['list_id'] = None
    updated['index'] = None
    response = client.put(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(4, 'item')}", headers=auth_headers(1), json=update)
    assert response.json() == updated
    assert response.status_code == 200
    # make sure it's not in the list
    response = client.get(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(2, 'item')}")
    list_item = get_item(2)
    list_item['contents']['metadata']['count'] = 1
    list_item['contents']['items'].pop(1)
    assert response.json() == list_item
    assert response.status_code == 200

def test_update_swap_lists(client, auth_headers, get_item):
    update = { "list_id": mock.to_uuid(2, 'item'), "index": 0 }
    updated = get_item(10)
    updated['list_id'] = mock.to_uuid(2, 'item')
    updated['index'] = 0
    response = client.put(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(10, 'item')}", headers=auth_headers(1), json=update)
    assert response.json() == updated
    assert response.status_code == 200
    # make sure it's in the new list
    response = client.get(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(2, 'item')}")
    list1 = get_item(2)
    list1['contents']['metadata']['count'] = 3
    list1['contents']['items'].insert(0, updated)
    list1['contents']['items'][1]['index'] = 1
    list1['contents']['items'][2]['index'] = 2
    assert response.json() == list1
    assert response.status_code == 200
    # make sure it's NOT in the old list
    response = client.get(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(9, 'item')}")
    list2 = get_item(9)
    list2['contents']['metadata']['count'] = 0
    list2['contents']['items'] = []
    assert response.json() == list2
    assert response.status_code == 200

def test_update_reorder1(client, auth_headers, get_item):
    update = { "list_id": mock.to_uuid(2, 'item'), "index": 2 }
    updated = get_item(3)
    updated['position'] = None
    updated['list_id'] = mock.to_uuid(2, 'item')
    updated['index'] = 1
    response = client.put(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(3, 'item')}", headers=auth_headers(1), json=update)
    assert response.json() == updated
    assert response.status_code == 200
    # make sure it's in the list
    response = client.get(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(2, 'item')}")
    list_item = get_item(2)
    list_item['contents']['items'][0], list_item['contents']['items'][1] = list_item['contents']['items'][1], list_item['contents']['items'][0]
    list_item['contents']['items'][0]['index'] = 0
    list_item['contents']['items'][1]['index'] = 1
    assert response.json() == list_item
    assert response.status_code == 200

def test_update_reorder2(client, auth_headers, get_item):
    update = { "index": 0 }
    updated = get_item(4)
    updated['position'] = None
    updated['list_id'] = mock.to_uuid(2, 'item')
    updated['index'] = 0
    response = client.put(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(4, 'item')}", headers=auth_headers(1), json=update)
    assert response.json() == updated
    assert response.status_code == 200
    # make sure it's in the list
    response = client.get(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(2, 'item')}")
    list_item = get_item(2)
    list_item['contents']['items'][0], list_item['contents']['items'][1] = list_item['contents']['items'][1], list_item['contents']['items'][0]
    list_item['contents']['items'][0]['index'] = 0
    list_item['contents']['items'][1]['index'] = 1
    assert response.json() == list_item
    assert response.status_code == 200

def test_update_insert_to_other_board_list(client, auth_headers, exception):
    update = { "list_id": mock.to_uuid(2, 'item'), "index": 1 }
    response = client.put(f"/boards/{mock.to_uuid(1, 'board')}/items/{mock.to_uuid(1, 'item')}", headers=auth_headers(1), json=update)
    assert response.json() == exception("entity_not_found", f"Unable to find item_list with id={mock.to_uuid(2, 'item')}")
    assert response.status_code == 404

def test_update_index_no_list(client, auth_headers, exception):
    update = { "index": 1 }
    response = client.put(f"/boards/{mock.to_uuid(1, 'board')}/items/{mock.to_uuid(1, 'item')}", headers=auth_headers(1), json=update)
    assert response.json() == exception("out_of_range", f"Index 1 out of range for item with id={mock.to_uuid(1, 'item')}")
    assert response.status_code == 422

def test_update_index_out_of_range_l(client, auth_headers, exception):
    update = { "list_id": mock.to_uuid(2, 'item'), "index": 3 }
    response = client.put(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(11, 'item')}", headers=auth_headers(1), json=update)
    assert response.json() == exception("out_of_range", f"Index 3 out of range for item_list with id={mock.to_uuid(2, 'item')}")
    assert response.status_code == 422

def test_update_index_out_of_range_s(client, auth_headers, exception):
    update = { "list_id": mock.to_uuid(2, 'item'), "index": -1 }
    response = client.put(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(11, 'item')}", headers=auth_headers(1), json=update)
    assert response.json() == exception("out_of_range", f"Index -1 out of range for item_list with id={mock.to_uuid(2, 'item')}")
    assert response.status_code == 422

def test_update_insert_list_to_list(client, auth_headers, exception):
    update = { "list_id": mock.to_uuid(2, 'item') }
    response = client.put(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(9, 'item')}", headers=auth_headers(1), json=update)
    assert response.json() == exception("add_list_to_list", "Cannot add a list to another list")
    assert response.status_code == 422

def test_update_insert_to_non_list(client, auth_headers, exception):
    update = { "list_id": mock.to_uuid(5, 'item') }
    response = client.put(f"/boards/{mock.to_uuid(1, 'board')}/items/{mock.to_uuid(1, 'item')}", headers=auth_headers(1), json=update)
    assert response.json() == exception("item_type_mismatch", f"Item with id={mock.to_uuid(5, 'item')} has type 'todo', but was treated as if it had type 'list'")
    assert response.status_code == 418

def test_delete_item(client, auth_headers, get_item, exception):
    response = client.delete(f"/boards/{mock.to_uuid(1, 'board')}/items/{mock.to_uuid(1, 'item')}", headers=auth_headers(1))
    assert response.status_code == 204
    # make sure it's gone
    response = client.get(f"/boards/{mock.to_uuid(1, 'board')}/items")
    assert response.json() == {
        "metadata": { "count": 2 },
        "items": [ get_item(5), get_item(7) ]
    }
    assert response.status_code == 200
    response = client.get(f"/boards/{mock.to_uuid(1, 'board')}/items/{mock.to_uuid(1, 'item')}")
    assert response.json() == exception('entity_not_found', f'Unable to find item with id={mock.to_uuid(1, 'item')}')
    assert response.status_code == 404

def test_delete_list_item(client, auth_headers, get_item):
    response = client.delete(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(3, 'item')}", headers=auth_headers(1))
    assert response.status_code == 204
    # make sure it's removed from the list
    response = client.get(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(2, 'item')}")
    list_item = get_item(2)
    list_item['contents']['metadata']['count'] = 1
    list_item['contents']['items'].pop(0)
    list_item['contents']['items'][0]['index'] = 0
    assert response.json() == list_item
    assert response.status_code == 200

def test_delete_list(client, auth_headers, get_item, exception):
    response = client.delete(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(2, 'item')}", headers=auth_headers(1))
    assert response.status_code == 204
    # make sure it and its items are deleted
    response = client.get(f"/boards/{mock.to_uuid(2, 'board')}/items")
    expected_items = [ get_item(6), get_item(9), get_item(11) ]
    # the list at id 9 connected to this, so make sure that connection vanishes
    expected_items[1]['pin']['connections'].remove(mock.to_uuid(1, 'pin'))
    assert response.json() == {
        "metadata": { "count": 3 },
        "items": expected_items
    }
    assert response.status_code == 200
    response = client.delete(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(3, 'item')}", headers=auth_headers(1))
    assert response.json() == exception('entity_not_found', f"Unable to find item with id={mock.to_uuid(3, 'item')}")
    assert response.status_code == 404
    response = client.delete(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(4, 'item')}", headers=auth_headers(1))
    assert response.json() == exception('entity_not_found', f"Unable to find item with id={mock.to_uuid(4, 'item')}")
    assert response.status_code == 404

def test_delete_404_item(client, auth_headers, exception):
    response = client.delete(f"/boards/{mock.to_uuid(1, 'board')}/items/{mock.to_uuid(404, 'item')}", headers=auth_headers(1))
    assert response.json() == exception('entity_not_found', f"Unable to find item with id={mock.to_uuid(404, 'item')}")
    assert response.status_code == 404

def test_delete_item_wrongboard(client, auth_headers, exception, get_item):
    response = client.delete(f"/boards/{mock.to_uuid(2, 'board')}/items/{mock.to_uuid(1, 'item')}", headers=auth_headers(1))
    assert response.json() == exception('entity_not_found', f"Unable to find item with id={mock.to_uuid(1, 'item')}")
    assert response.status_code == 404
    # make sure it's still there
    response = client.get(f"/boards/{mock.to_uuid(1, 'board')}/items/{mock.to_uuid(1, 'item')}")
    assert response.json() == get_item(1)
    assert response.status_code == 200

def test_delete_item_unauthorized(client, auth_headers, exception, get_item):
    response = client.delete(f"/boards/{mock.to_uuid(1, 'board')}/items/{mock.to_uuid(1, 'item')}", headers=auth_headers(4))
    assert response.json() == exception("no_permissions", f"No permissions to modify board on board with id={mock.to_uuid(1, 'board')}")
    assert response.status_code == 403
    # make sure it's still there
    response = client.get(f"/boards/{mock.to_uuid(1, 'board')}/items/{mock.to_uuid(1, 'item')}")
    assert response.json() == get_item(1)
    assert response.status_code == 200

def test_delete_item_private(client, auth_headers, exception):
    response = client.delete(f"/boards/{mock.to_uuid(3, 'board')}/items/{mock.to_uuid(8, 'item')}", headers=auth_headers(3))
    assert response.status_code == 204
    response = client.get(f"/boards/{mock.to_uuid(3, 'board')}/items/{mock.to_uuid(8, 'item')}", headers=auth_headers(3))
    assert response.json() == exception('entity_not_found', f"Unable to find item with id={mock.to_uuid(8, 'item')}")
    assert response.status_code == 404

def test_delete_item_private_unauthorized(client, auth_headers, exception, get_item):
    response = client.delete(f"/boards/{mock.to_uuid(3, 'board')}/items/{mock.to_uuid(8, 'item')}", headers=auth_headers(4))
    assert response.json() == exception('entity_not_found', f"Unable to find board with id={mock.to_uuid(3, 'board')}")
    assert response.status_code == 404
    # make sure it's still there
    response = client.get(f"/boards/{mock.to_uuid(3, 'board')}/items/{mock.to_uuid(8, 'item')}", headers=auth_headers(3))
    assert response.json() == get_item(8)
    assert response.status_code == 200