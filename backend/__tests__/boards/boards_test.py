"""Module for testing the board routes"""

from backend.__tests__ import mock

def test_get_public(client, get_board):
    # boards 1 and 2 are public
    response = client.get("/boards")
    assert response.json() == {
        "metadata": { "count": 2 },
        "boards": [ get_board(2), get_board(1) ] # they are ordered by name
    }
    assert response.status_code == 200

def test_get_visible(client, get_board, auth_headers):
    # boards 1 and 2 are public, and account 2 owns board 3
    response = client.get("/boards", headers=auth_headers(2))
    assert response.json() == {
        "metadata": { "count": 3 },
        "boards": [ get_board(2), get_board(3), get_board(1) ] # they are ordered by name
    }
    assert response.status_code == 200

def test_get_editable(client, auth_headers, get_board):
    # account 2 is the owner of board 3 and an editor on board 1, and thus should not see board 2
    response = client.get("/boards/editable", headers=auth_headers(2))
    assert response.json() == {
        "metadata": { "count": 2 },
        "boards": [ get_board(3), get_board(1) ]
    }
    assert response.status_code == 200

def test_get_public_board(client, get_board):
    response = client.get(f"/boards/{mock.to_uuid(1, 'board')}")
    assert response.json() == get_board(1)
    assert response.status_code == 200

def test_get_404_board(client, exception):
    response = client.get(f"/boards/{mock.to_uuid(404, 'board')}")
    assert response.json() == exception("entity_not_found", f"Unable to find board with id={mock.to_uuid(404, 'board')}")
    assert response.status_code == 404

def test_get_private_board(client, auth_headers, get_board):
    response = client.get(f"/boards/{mock.to_uuid(3, 'board')}", headers=auth_headers(2))
    assert response.json() == get_board(3)
    assert response.status_code == 200

def test_get_private_board_unauthorized(client, auth_headers, exception):
    response = client.get(f"/boards/{mock.to_uuid(3, 'board')}", headers=auth_headers(4))
    assert response.json() == exception("entity_not_found", f"Unable to find board with id={mock.to_uuid(3, 'board')}") # the board exists, but even just saying that gives too much information
    assert response.status_code == 404

def test_create_board(client, boards, auth_headers):
    data = {
        "name": "created"
    }
    mock.last_uuid = mock.OFFSETS['board'] + len(boards)
    response = client.post("/boards", headers=auth_headers(4), json=data)
    assert response.json() == {
        "id": mock.to_uuid(4, 'board'),
        "name": "created",
        "icon": "default",
        "owner_id": mock.to_uuid(4, 'account'),
        "public": False,
    }
    assert response.status_code == 201

def test_update_board(client, auth_headers):
    data = {
        "icon": "sun",
        "public": False
    }
    response = client.put(f"/boards/{mock.to_uuid(1, 'board')}", headers=auth_headers(1), json=data)
    assert response.json() == {
        "id": mock.to_uuid(1, 'board'),
        "name": "parent",
        "icon": "sun",
        "owner_id": mock.to_uuid(1, 'account'),
        "public": False
    }
    assert response.status_code == 200

def test_update_board_as_editor(client, auth_headers, exception):
    data = {
        "icon": "sun",
        "public": False
    }
    response = client.put(f"/boards/{mock.to_uuid(1, 'board')}", headers=auth_headers(2), json=data) # account 2 is an editor on this board but not an owner
    assert response.json() == exception("access_denied", "Access denied")
    assert response.status_code == 403

def test_update_board_unauthorized(client, auth_headers, exception):
    data = {
        "public": True
    }
    response = client.put(f"/boards/{mock.to_uuid(3, 'board')}", headers=auth_headers(4), json=data) # account 4 has no knowledge of this board
    assert response.json() == exception("entity_not_found", f"Unable to find board with id={mock.to_uuid(3, 'board')}")
    assert response.status_code == 404

def test_delete_board(client, auth_headers, exception):
    response = client.delete(f"/boards/{mock.to_uuid(3, 'board')}", headers=auth_headers(2))
    assert response.status_code == 204
    response = client.get(f"/boards/{mock.to_uuid(3, 'board')}", headers=auth_headers(2))
    assert response.json() == exception("entity_not_found", f"Unable to find board with id={mock.to_uuid(3, 'board')}")
    assert response.status_code == 404

def test_delete_board_as_editor(client, auth_headers, exception):
    response = client.delete(f"/boards/{mock.to_uuid(3, 'board')}", headers=auth_headers(1))
    assert response.json() == exception("access_denied", "Access denied")
    assert response.status_code == 403

def test_delete_board_unauthorized(client, auth_headers, exception):
    response = client.delete(f"/boards/{mock.to_uuid(3, 'board')}", headers=auth_headers(4)) # account 4 has no knowledge of this board
    assert response.json() == exception("entity_not_found", f"Unable to find board with id={mock.to_uuid(3, 'board')}")
    assert response.status_code == 404

def test_get_editors(client, auth_headers, get_response_account):
    response = client.get(f"/boards/{mock.to_uuid(3, 'board')}/editors", headers=auth_headers(2))
    assert response.json() == {
        "metadata": { "count": 2 }, 
        "accounts": [ get_response_account(1), get_response_account(3) ] # TODO: Figure out ordering
    }
    assert response.status_code == 200

def test_add_editor(client, auth_headers, get_response_account):
    response = client.put(f"/boards/{mock.to_uuid(3, 'board')}/editors/{mock.to_uuid(4, 'account')}", headers=auth_headers(2))
    assert response.json() == {
        "metadata": { "count": 3 }, 
        "accounts": [ get_response_account(1), get_response_account(3), get_response_account(4) ] # TODO: Figure out ordering
    }
    assert response.status_code == 201

def test_remove_editor(client, auth_headers, get_response_account):
    response = client.delete(f"/boards/{mock.to_uuid(3, 'board')}/editors/{mock.to_uuid(3, 'account')}", headers=auth_headers(2))
    assert response.json() == {
        "metadata": { "count": 1 }, 
        "accounts": [ get_response_account(1) ]
    }
    assert response.status_code == 200

def test_add_owner_as_editor(client, auth_headers, exception):
    response = client.put(f"/boards/{mock.to_uuid(3, 'board')}/editors/{mock.to_uuid(2, 'account')}", headers=auth_headers(2))
    assert response.json() == exception("add_board_owner_as_editor", "Cannot add the board owner as an editor")
    assert response.status_code == 422