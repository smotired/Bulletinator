"""Tests that staff accounts can do actions they wouldn't normally be allowed to do"""

# Account 5 is not referenced at all so would normally have the permissions of a logged-out user, but they're staff so should be able to override

from backend.__tests__ import mock

def test_view_private_board(client, auth_headers, get_board):
    response = client.get(f"/boards/{mock.to_uuid(3, 'board')}", headers=auth_headers(5))
    assert response.json() == get_board(3)
    assert response.status_code == 200

def test_update_board(client, auth_headers, get_board):
    update = { "name": "Updated by Staff" }
    response = client.put(f"/boards/{mock.to_uuid(1, 'board')}", headers=auth_headers(5), json=update)
    assert response.json() == { **get_board(1), **update }
    assert response.status_code == 200

def test_update_private_board(client, auth_headers, get_board):
    update = { "name": "Updated by Staff" }
    response = client.put(f"/boards/{mock.to_uuid(3, 'board')}", headers=auth_headers(5), json=update)
    assert response.json() == { **get_board(3), **update }
    assert response.status_code == 200

def test_delete_board(client, auth_headers):
    response = client.delete(f"/boards/{mock.to_uuid(1, 'board')}", headers=auth_headers(5))
    assert response.status_code == 204

def test_delete_private_board(client, auth_headers):
    response = client.delete(f"/boards/{mock.to_uuid(3, 'board')}", headers=auth_headers(5))
    assert response.status_code == 204

def test_transfer_board(client, auth_headers, get_board):
    transfer = { "account_id": mock.to_uuid(1, 'account') }
    response = client.post(f"/boards/{mock.to_uuid(3, 'board')}/transfer", headers=auth_headers(5), json=transfer)
    assert response.json() == { **get_board(3), "owner_id": transfer['account_id'] }
    assert response.status_code == 200

def test_get_editors(client, auth_headers, get_response_account):
    response = client.get(f"/boards/{mock.to_uuid(3, 'board')}/editors", headers=auth_headers(5))
    assert response.json() == {
        "metadata": { "count": 2 },
        "accounts": [ get_response_account(1), get_response_account(3) ]
    }
    assert response.status_code == 200

def test_add_editor(client, auth_headers, get_response_account):
    response = client.put(f"/boards/{mock.to_uuid(3, 'board')}/editors/{mock.to_uuid(4, 'account')}", headers=auth_headers(5))
    assert response.json() == {
        "metadata": { "count": 3 },
        "accounts": [ get_response_account(1), get_response_account(3), get_response_account(4) ]
    }
    assert response.status_code == 201

def test_remove_editor(client, auth_headers, get_response_account):
    response = client.delete(f"/boards/{mock.to_uuid(3, 'board')}/editors/{mock.to_uuid(3, 'account')}", headers=auth_headers(5))
    assert response.json() == {
        "metadata": { "count": 1 },
        "accounts": [ get_response_account(1) ]
    }
    assert response.status_code == 200

def test_modify_board(client, auth_headers, items, get_item):
    """Add an item. We don't need to do any more tests because they all use the same permission logic."""
    item = {
        "list_id": None,
        "position": "200,200",
        "index": None,
        "type": "note",
        "text": "Created Note",
    }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(3, 'board')}/items", headers=auth_headers(5), json=item)
    updated_item = {
        "id": mock.to_uuid(len(items) + 1, 'item'),
        "board_id": mock.to_uuid(3, 'board'),
        "pin": None,
        **item,
    }
    assert response.json() == updated_item
    assert response.status_code == 201
    response = client.get(f"/boards/{mock.to_uuid(3, 'board')}/items", headers=auth_headers(5))
    assert response.json() == {
        "metadata": { "count": 2 },
        "items": [ get_item(8), updated_item ]
    }
    assert response.status_code == 200