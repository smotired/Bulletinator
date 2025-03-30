"""Module for testing the board routes"""
from backend.database.schema import *

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

def test_create_board():
    pass

def test_update_board():
    pass

def test_update_board_unauthorized():
    pass

def test_delete_board():
    pass

def test_delete_board_unauthorized():
    pass