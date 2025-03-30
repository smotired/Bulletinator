"""Module for testing the board routes"""
from backend.database.schema import *

def test_get_editable(client,auth_headers, get_board):
    # user 2 is the owner of board 3 and an editor on board 1
    response = client.get("/boards/editable", headers=auth_headers(2))
    assert response.json() == {
        "metadata": { "count": 2 },
        "boards": [ get_board(3), get_board(1) ] # they are ordered by name
    }
    assert response.status_code == 200