"""Module for testing the board routes"""

def test_get_public(client, get_board):
    # boards 1 and 2 are public
    response = client.get("/boards")
    assert response.json() == {
        "metadata": { "count": 2 },
        "boards": [ get_board(2), get_board(1) ] # they are ordered by name
    }
    assert response.status_code == 200

def test_get_visible(client, get_board, auth_headers):
    # boards 1 and 2 are public, and user 2 owns board 3
    response = client.get("/boards", headers=auth_headers(2))
    assert response.json() == {
        "metadata": { "count": 3 },
        "boards": [ get_board(2), get_board(3), get_board(1) ] # they are ordered by name
    }
    assert response.status_code == 200

def test_get_editable(client, auth_headers, get_board):
    # user 2 is the owner of board 3 and an editor on board 1, and thus should not see board 2
    response = client.get("/boards/editable", headers=auth_headers(2))
    assert response.json() == {
        "metadata": { "count": 2 },
        "boards": [ get_board(3), get_board(1) ]
    }
    assert response.status_code == 200

def test_get_public_board(client, get_board):
    response = client.get("/boards/1")
    assert response.json() == get_board(1)
    assert response.status_code == 200

def test_get_404_board(client, exception):
    response = client.get("/boards/404")
    assert response.json() == exception("entity_not_found", "Unable to find board with id=404")
    assert response.status_code == 404

def test_get_private_board(client, auth_headers, get_board):
    response = client.get("/boards/3", headers=auth_headers(2))
    assert response.json() == get_board(3)
    assert response.status_code == 200

def test_get_private_board_unauthorized(client, auth_headers, exception):
    response = client.get("/boards/3", headers=auth_headers(4))
    assert response.json() == exception("entity_not_found", "Unable to find board with id=3") # the board exists, but even just saying that gives too much information
    assert response.status_code == 404

def test_create_board(client, auth_headers):
    data = {
        "name": "created"
    }
    response = client.post("/boards", headers=auth_headers(4), json=data)
    assert response.json() == {
        "id": 4,
        "name": "created",
        "icon": "default",
        "owner_id": 4,
        "public": False,
    }
    assert response.status_code == 201

def test_update_board(client, auth_headers):
    data = {
        "icon": "sun",
        "public": False
    }
    response = client.put("/boards/1", headers=auth_headers(1), json=data)
    assert response.json() == {
        "id": 1,
        "name": "parent",
        "icon": "sun",
        "owner_id": 1,
        "public": False
    }
    assert response.status_code == 200

def test_update_board_as_editor(client, auth_headers, exception):
    data = {
        "icon": "sun",
        "public": False
    }
    response = client.put("/boards/1", headers=auth_headers(2), json=data) # user 2 is an editor on this board but not an owner
    assert response.json() == exception("access_denied", "Access denied")
    assert response.status_code == 403

def test_update_board_unauthorized(client, auth_headers, exception):
    data = {
        "public": True
    }
    response = client.put("/boards/3", headers=auth_headers(4), json=data) # user 4 has no knowledge of this board
    assert response.json() == exception("entity_not_found", "Unable to find board with id=3")
    assert response.status_code == 404

def test_delete_board(client, auth_headers, exception):
    response = client.delete("/boards/3", headers=auth_headers(2))
    assert response.status_code == 204
    response = client.get("/boards/3", headers=auth_headers(2))
    assert response.json() == exception("entity_not_found", "Unable to find board with id=3")
    assert response.status_code == 404

def test_delete_board_as_editor(client, auth_headers, exception):
    response = client.delete("/boards/3", headers=auth_headers(1))
    assert response.json() == exception("access_denied", "Access denied")
    assert response.status_code == 403

def test_delete_board_unauthorized(client, auth_headers, exception):
    response = client.delete("/boards/3", headers=auth_headers(4)) # user 4 has no knowledge of this board
    assert response.json() == exception("entity_not_found", "Unable to find board with id=3")
    assert response.status_code == 404

def test_get_editors(client, auth_headers, get_response_user):
    response = client.get("/boards/3/editors", headers=auth_headers(2))
    assert response.json() == {
        "metadata": { "count": 2 }, 
        "users": [ get_response_user(1), get_response_user(3) ]
    }
    assert response.status_code == 200

def test_add_editor(client, auth_headers, get_response_user):
    response = client.put("/boards/3/editors/4", headers=auth_headers(2))
    assert response.json() == {
        "metadata": { "count": 3 }, 
        "users": [ get_response_user(1), get_response_user(3), get_response_user(4) ]
    }
    assert response.status_code == 201

def test_remove_editor(client, auth_headers, get_response_user):
    response = client.delete("/boards/3/editors/3", headers=auth_headers(2))
    assert response.json() == {
        "metadata": { "count": 1 }, 
        "users": [ get_response_user(1) ]
    }
    assert response.status_code == 200

def test_add_owner_as_editor(client, auth_headers, exception):
    response = client.put("/boards/3/editors/2", headers=auth_headers(2))
    assert response.json() == exception("add_board_owner_as_editor", "Cannot add the board owner as an editor")
    assert response.status_code == 403