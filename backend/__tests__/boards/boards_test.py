"""Module for testing the board routes"""

from sqlalchemy import select
from backend.__tests__ import mock
from backend.database.schema import DBEditorInvitation

def test_get_public(client, get_board):
    # boards 1 and 2 are public
    response = client.get("/boards")
    assert response.json() == {
        "metadata": { "count": 2 },
        "contents": [ get_board(2), get_board(1) ] # they are ordered by name
    }
    assert response.status_code == 200

def test_get_visible(client, get_board, auth_headers):
    # boards 1 and 2 are public, and account 2 owns board 3
    response = client.get("/boards", headers=auth_headers(2))
    assert response.json() == {
        "metadata": { "count": 3 },
        "contents": [ get_board(2), get_board(3), get_board(1) ] # they are ordered by name
    }
    assert response.status_code == 200

def test_get_editable(client, auth_headers, get_board):
    # account 2 is the owner of board 3 and an editor on board 1, and thus should not see board 2
    response = client.get("/boards/editable", headers=auth_headers(2))
    assert response.json() == {
        "metadata": { "count": 2 },
        "contents": [ get_board(3), get_board(1) ]
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

def test_get_by_name_id(client, get_board):
    response = client.get(f"/boards/alice-parent")
    assert response.json() == get_board(1)
    assert response.status_code == 200

def test_get_by_name_id_private(client, auth_headers, get_board):
    response = client.get(f"/boards/bob-other", headers=auth_headers(2))
    assert response.json() == get_board(3)
    assert response.status_code == 200

def test_get_by_name_id_private_unauth(client, auth_headers, exception):
    response = client.get(f"/boards/bob-other", headers=auth_headers(4))
    assert response.json() == exception("entity_not_found", f"Unable to find board with identifier=other")
    assert response.status_code == 404

def test_get_by_name_id_no_name(client, exception):
    response = client.get(f"/boards/nobody-parent")
    assert response.json() == exception("entity_not_found", f"Unable to find account with username=nobody")
    assert response.status_code == 404

def test_get_by_name_id_no_board(client, exception):
    response = client.get(f"/boards/alice-noboard")
    assert response.json() == exception("entity_not_found", f"Unable to find board with identifier=noboard")
    assert response.status_code == 404

def test_get_by_name_id_mismatch(client, exception):
    response = client.get(f"/boards/david-parent")
    assert response.json() == exception("entity_not_found", f"Unable to find board with identifier=parent")
    assert response.status_code == 404

def test_get_by_name_id_mismatch_editor(client, exception):
    response = client.get(f"/boards/bob-parent")
    assert response.json() == exception("entity_not_found", f"Unable to find board with identifier=parent")
    assert response.status_code == 404

def test_create_board(client, boards, auth_headers):
    data = {
        "name": "created"
    }
    mock.last_uuid = mock.OFFSETS['board'] + len(boards)
    response = client.post("/boards", headers=auth_headers(4), json=data)
    assert response.json() == {
        "id": mock.to_uuid(4, 'board'),
        "identifier": "created",
        "name": "created",
        "icon": "default",
        "owner_id": mock.to_uuid(4, 'account'),
        "public": False,
    }
    assert response.status_code == 201

def test_create_board_identifier(client, boards, auth_headers):
    data = {
        "name": "Cr 4-z&y_-- _ w(4*cKy--)-n^^4^^\"m^^E"
    }
    mock.last_uuid = mock.OFFSETS['board'] + len(boards)
    response = client.post("/boards", headers=auth_headers(4), json=data)
    assert response.json() == {
        "id": mock.to_uuid(4, 'board'),
        "identifier": "Cr_4_zy_w4cKy_n4mE",
        "name": "Cr 4-z&y_-- _ w(4*cKy--)-n^^4^^\"m^^E",
        "icon": "default",
        "owner_id": mock.to_uuid(4, 'account'),
        "public": False,
    }
    assert response.status_code == 201

def test_create_board_invalid_identifier(client, boards, auth_headers, exception):
    data = {
        "name": "created",
        "identifier": "Specified But Invalid Identifier",
    }
    mock.last_uuid = mock.OFFSETS['board'] + len(boards)
    response = client.post("/boards", headers=auth_headers(1), json=data)
    assert response.json() == exception("invalid_field", f"Value '{data['identifier']}' is invalid for field 'identifier'")
    assert response.status_code == 422

def test_create_board_taken_identifier(client, boards, auth_headers, exception):
    data = {
        "name": "created",
        "identifier": "parent",
    }
    mock.last_uuid = mock.OFFSETS['board'] + len(boards)
    response = client.post("/boards", headers=auth_headers(1), json=data)
    assert response.json() == exception("duplicate_entity", "Entity board with identifier=parent already exists")
    assert response.status_code == 422

def test_create_board_taken_identifier_by_other_account(client, boards, auth_headers):
    data = {
        "name": "created",
        "identifier": "other",
    }
    mock.last_uuid = mock.OFFSETS['board'] + len(boards)
    response = client.post("/boards", headers=auth_headers(4), json=data)
    assert response.json() == {
        "id": mock.to_uuid(4, 'board'),
        "identifier": "other",
        "name": "created",
        "icon": "default",
        "owner_id": mock.to_uuid(4, 'account'),
        "public": False,
    }
    assert response.status_code == 201

def test_update_board(client, auth_headers):
    data = {
        "identifier": "updated_parent",
        "icon": "sun",
        "public": False
    }
    response = client.put(f"/boards/{mock.to_uuid(1, 'board')}", headers=auth_headers(1), json=data)
    assert response.json() == {
        "id": mock.to_uuid(1, 'board'),
        "identifier": "updated_parent",
        "name": "parent",
        "icon": "sun",
        "owner_id": mock.to_uuid(1, 'account'),
        "public": False
    }
    assert response.status_code == 200

def test_update_board_invalid_identifier(client, auth_headers, exception):
    data = {
        "identifier": "Specified But Invalid Identifier",
    }
    response = client.put(f"/boards/{mock.to_uuid(1, 'board')}", headers=auth_headers(1), json=data)
    assert response.json() == exception("invalid_field", f"Value '{data['identifier']}' is invalid for field 'identifier'")
    assert response.status_code == 422

def test_update_board_taken_identifier(client, auth_headers, exception):
    data = {
        "identifier": "child",
    }
    response = client.put(f"/boards/{mock.to_uuid(1, 'board')}", headers=auth_headers(1), json=data)
    assert response.json() == exception("duplicate_entity", "Entity board with identifier=child already exists")
    assert response.status_code == 422

def test_update_board_taken_by_other_account(client, auth_headers, get_board):
    data = {
        "identifier": "other",
    }
    response = client.put(f"/boards/{mock.to_uuid(1, 'board')}", headers=auth_headers(1), json=data)
    assert response.json() == {
        **get_board(1),
        **data,
    }
    assert response.status_code == 200

def test_update_board_as_editor(client, auth_headers, exception):
    data = {
        "icon": "sun",
        "public": False
    }
    response = client.put(f"/boards/{mock.to_uuid(1, 'board')}", headers=auth_headers(2), json=data) # account 2 is an editor on this board but not an owner
    assert response.json() == exception("no_permissions", f"No permissions to manage board on board with id={mock.to_uuid(1, 'board')}")
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
    assert response.json() == exception("no_permissions", f"No permissions to delete board on board with id={mock.to_uuid(3, 'board')}")
    assert response.status_code == 403

def test_delete_board_unauthorized(client, auth_headers, exception):
    response = client.delete(f"/boards/{mock.to_uuid(3, 'board')}", headers=auth_headers(4)) # account 4 has no knowledge of this board
    assert response.json() == exception("entity_not_found", f"Unable to find board with id={mock.to_uuid(3, 'board')}")
    assert response.status_code == 404

def test_get_editors(client, auth_headers, get_response_account):
    response = client.get(f"/boards/{mock.to_uuid(3, 'board')}/editors", headers=auth_headers(2))
    assert response.json() == {
        "metadata": { "count": 2 }, 
        "contents": [ get_response_account(1), get_response_account(3) ] # TODO: Figure out ordering
    }
    assert response.status_code == 200

def test_get_editors_as_editor(client, auth_headers, get_response_account):
    response = client.get(f"/boards/{mock.to_uuid(3, 'board')}/editors", headers=auth_headers(1))
    assert response.json() == {
        "metadata": { "count": 2 }, 
        "contents": [ get_response_account(1), get_response_account(3) ]
    }
    assert response.status_code == 200

def test_get_editors_private(client, exception, auth_headers):
    response = client.get(f"/boards/{mock.to_uuid(1, 'board')}/editors", headers=auth_headers(4))
    assert response.json() == exception("no_permissions", f"No permissions to view editors on board with id={mock.to_uuid(1, "board")}")
    assert response.status_code == 403

def test_invite_editor(session, client, auth_headers, get_response_account, get_board):
    mock.last_uuid = mock.OFFSETS['account'] + 100
    response = client.post(f"/boards/{mock.to_uuid(3, 'board')}/editors", headers=auth_headers(2), json={ "email": "david@example.com" })
    assert response.status_code == 204
    # Make sure an invitation was created
    statement = select(DBEditorInvitation).where(DBEditorInvitation.email == "david@example.com")
    results = list( session.execute(statement).scalars().all() )
    assert len(results) == 1
    invitation = results[0].__dict__.copy()
    del invitation['_sa_instance_state']
    del invitation['expires_at']
    assert invitation == {
        "id": mock.to_uuid(101, 'account'),
        "board_id": mock.to_uuid(3, 'board'),
        "email": "david@example.com",
    }
    # Accept the invitation
    response = client.post(f"/boards/accept-invite/{mock.to_uuid(101, 'account')}")
    assert response.json() == get_board(3)
    assert response.status_code == 200
    # Make sure they are truly an editor now
    response = client.get(f"/boards/{mock.to_uuid(3, 'board')}/editors", headers=auth_headers(4))
    assert response.json() == {
        "metadata": { "count": 3 }, 
        "contents": [ get_response_account(1), get_response_account(3), get_response_account(4) ]
    }
    assert response.status_code == 200

def test_invite_existing_editor(session, client, auth_headers):
    mock.last_uuid = mock.OFFSETS['account'] + 100
    response = client.post(f"/boards/{mock.to_uuid(3, 'board')}/editors", headers=auth_headers(2), json={ "email": "charlie@example.com" })
    assert response.status_code == 204
    # Make sure no invitation was created
    statement = select(DBEditorInvitation).where(DBEditorInvitation.email == "charlie@example.com")
    results = list( session.execute(statement).scalars().all() )
    assert len(results) == 0

def test_invite_editor_as_editor(client, auth_headers, exception):
    response = client.post(f"/boards/{mock.to_uuid(3, 'board')}/editors", headers=auth_headers(3), json={ "email": "david@example.com" })
    assert response.json() == exception("no_permissions", f"No permissions to manage editors on board with id={mock.to_uuid(3, "board")}")
    assert response.status_code == 403

def test_invite_editor_unauth(client, auth_headers, exception):
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/editors", headers=auth_headers(4), json={ "email": "david@example.com" })
    assert response.json() == exception("no_permissions", f"No permissions to manage editors on board with id={mock.to_uuid(1, "board")}")
    assert response.status_code == 403

def test_remove_editor(client, auth_headers, get_response_account):
    response = client.delete(f"/boards/{mock.to_uuid(3, 'board')}/editors/{mock.to_uuid(3, 'account')}", headers=auth_headers(2))
    assert response.json() == {
        "metadata": { "count": 1 }, 
        "contents": [ get_response_account(1) ]
    }
    assert response.status_code == 200

def test_remove_editor_as_editor(client, auth_headers, exception, get_response_account):
    response = client.delete(f"/boards/{mock.to_uuid(3, 'board')}/editors/{mock.to_uuid(3, 'account')}", headers=auth_headers(1))
    assert response.json() == exception("no_permissions", f"No permissions to manage editors on board with id={mock.to_uuid(3, "board")}")
    assert response.status_code == 403
    response = client.get(f"/boards/{mock.to_uuid(3, 'board')}/editors", headers=auth_headers(1))
    assert response.json() == {
        "metadata": { "count": 2 }, 
        "contents": [ get_response_account(1), get_response_account(3) ]
    }
    assert response.status_code == 200

def test_remove_editor_as_self(client, auth_headers, get_response_account):
    response = client.delete(f"/boards/{mock.to_uuid(3, 'board')}/editors/{mock.to_uuid(3, 'account')}", headers=auth_headers(3))
    assert response.json() == {
        "metadata": { "count": 1 }, 
        "contents": [ get_response_account(1) ]
    }
    assert response.status_code == 200

def test_invite_owner_as_editor(client, auth_headers, exception):
    response = client.post(f"/boards/{mock.to_uuid(3, 'board')}/editors", headers=auth_headers(2), json={ "email": "bob@example.com" })
    assert response.json() == exception("add_board_owner_as_editor", "Cannot add the board owner as an editor")
    assert response.status_code == 422

def test_transfer(client, auth_headers, get_board, get_response_account):
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/transfer", headers=auth_headers(1), json={"account_id": mock.to_uuid(2, 'account')})
    assert response.json() == {
        **get_board(1),
        "owner_id": mock.to_uuid(2, 'account'),
    }
    assert response.status_code == 200
    response = client.get(f"/boards/{mock.to_uuid(1, 'board')}/editors", headers=auth_headers(2))
    assert response.json() == {
        "metadata": { "count": 1 },
        "contents": [ get_response_account(1) ],
    }
    assert response.status_code == 200

def test_transfer_as_editor(client, auth_headers, exception):
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/transfer", headers=auth_headers(2), json={"account_id": mock.to_uuid(2, 'account')})
    assert response.json() == exception("no_permissions", f"No permissions to transfer board on board with id={mock.to_uuid(1, 'board')}")
    assert response.status_code == 403

def test_transfer_as_random(client, auth_headers, exception):
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/transfer", headers=auth_headers(4), json={"account_id": mock.to_uuid(4, 'account')})
    assert response.json() == exception("no_permissions", f"No permissions to transfer board on board with id={mock.to_uuid(1, 'board')}")
    assert response.status_code == 403

def test_transfer_private(client, auth_headers, get_board, get_response_account):
    response = client.post(f"/boards/{mock.to_uuid(3, 'board')}/transfer", headers=auth_headers(2), json={"account_id": mock.to_uuid(1, 'account')})
    assert response.json() == {
        **get_board(3),
        "owner_id": mock.to_uuid(1, 'account'),
    }
    assert response.status_code == 200
    response = client.get(f"/boards/{mock.to_uuid(1, 'board')}/editors", headers=auth_headers(2))
    assert response.json() == {
        "metadata": { "count": 1 },
        "contents": [ get_response_account(2) ],
    }
    assert response.status_code == 200

def test_transfer_private_unauth(client, auth_headers, exception):
    response = client.post(f"/boards/{mock.to_uuid(3, 'board')}/transfer", headers=auth_headers(4), json={"account_id": mock.to_uuid(1, 'account')})
    assert response.json() == exception("entity_not_found", f"Unable to find board with id={mock.to_uuid(3, 'board')}")
    assert response.status_code == 404

def test_transfer_to_non_editor(client, auth_headers, exception):
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/transfer", headers=auth_headers(1), json={"account_id": mock.to_uuid(4, 'account')})
    assert response.json() == exception("invalid_operation", f"Cannot transfer board with id={mock.to_uuid(1, 'board')} to account with id={mock.to_uuid(4, 'account')}")
    assert response.status_code == 422

def test_transfer_to_self(client, auth_headers, exception):
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/transfer", headers=auth_headers(1), json={"account_id": mock.to_uuid(1, 'account')})
    assert response.json() == exception("invalid_operation", f"Cannot transfer board with id={mock.to_uuid(1, 'board')} to account with id={mock.to_uuid(1, 'account')}")
    assert response.status_code == 422

def test_create_with_reference(client, auth_headers, boards, get_response_account):
    data = {
        "name": "referencer",
        "reference_id": mock.to_uuid(1, 'board'),
    }
    mock.last_uuid = mock.OFFSETS['board'] + len(boards)
    response = client.post("/boards", headers=auth_headers(1), json=data)
    assert response.json() == {
        "id": mock.to_uuid(len(boards)+1, 'board'),
        "identifier": "referencer",
        "name": "referencer",
        "icon": "default",
        "owner_id": mock.to_uuid(1, 'account'),
        "public": False,
    }
    assert response.status_code == 201
    # Make sure editors can automatically edit the new board
    response = client.get(f"/boards/{mock.to_uuid(len(boards)+1, 'board')}/editors", headers=auth_headers(1))
    assert response.json() == {
        "metadata": { "count": 1 },
        "contents": [ get_response_account(2) ],
    }
    assert response.status_code == 200

def test_create_with_reference_as_editor(client, auth_headers, boards, get_response_account):
    data = {
        "name": "referencer",
        "reference_id": mock.to_uuid(1, 'board'),
    }
    mock.last_uuid = mock.OFFSETS['board'] + len(boards)
    response = client.post("/boards", headers=auth_headers(2), json=data)
    assert response.json() == {
        "id": mock.to_uuid(len(boards)+1, 'board'),
        "identifier": "referencer",
        "name": "referencer",
        "icon": "default",
        "owner_id": mock.to_uuid(2, 'account'),
        "public": False,
    }
    assert response.status_code == 201
    # Make sure owner of the reference board can automatically edit the new board
    response = client.get(f"/boards/{mock.to_uuid(len(boards)+1, 'board')}/editors", headers=auth_headers(2))
    assert response.json() == {
        "metadata": { "count": 1 },
        "contents": [ get_response_account(1) ],
    }
    assert response.status_code == 200

def test_create_with_reference_as_non_editor(client, auth_headers, boards, exception):
    data = {
        "name": "referencer",
        "reference_id": mock.to_uuid(1, 'board'),
    }
    mock.last_uuid = mock.OFFSETS['board'] + len(boards)
    response = client.post("/boards", headers=auth_headers(3), json=data)
    assert response.json() == exception("no_permissions", f"No permissions to reference board on board with id={data['reference_id']}")
    assert response.status_code == 403

def test_create_with_reference_private_unauth(client, auth_headers, boards, exception):
    data = {
        "name": "referencer",
        "reference_id": mock.to_uuid(3, 'board'),
    }
    mock.last_uuid = mock.OFFSETS['board'] + len(boards)
    response = client.post("/boards", headers=auth_headers(4), json=data)
    assert response.json() == exception("entity_not_found", f"Unable to find board with id={data['reference_id']}")
    assert response.status_code == 404

def test_create_with_reference_nonexistent(client, auth_headers, boards, exception):
    data = {
        "name": "referencer",
        "reference_id": mock.to_uuid(404, 'board'),
    }
    mock.last_uuid = mock.OFFSETS['board'] + len(boards)
    response = client.post("/boards", headers=auth_headers(4), json=data)
    assert response.json() == exception("entity_not_found", f"Unable to find board with id={data['reference_id']}")
    assert response.status_code == 404