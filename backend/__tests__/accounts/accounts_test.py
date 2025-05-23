"""Tests for managing accounts"""

from backend.config import settings
from backend.__tests__ import mock
from backend.database.schema import DBAccount

def test_get_accounts(client, get_response_account):
    response = client.get("/accounts")
    assert response.json() == {
        "metadata": { "count": 5 },
        "contents": [ get_response_account(1), get_response_account(2), get_response_account(3), get_response_account(4), get_response_account(5) ]
    }
    assert response.status_code == 200

def test_get_account(client, get_response_account):
    response = client.get(f"/accounts/{mock.to_uuid(1, 'account')}")
    assert response.json() == get_response_account(1)
    assert response.status_code == 200

def test_get_by_username(client, get_response_account):
    response = client.get(f"/accounts/alice")
    assert response.json() == get_response_account(1)
    assert response.status_code == 200

def test_get_by_username_404(client, exception):
    response = client.get(f"/accounts/nobody")
    assert response.json() == exception('entity_not_found', "Unable to find account with username=nobody")
    assert response.status_code == 404

# No tests for creating accounts because that's handled in registrating

def test_update_account(client, auth_headers, get_account):
    update = {
        "username": "updated_alice",
        "profile_image": "/static/images/test_image.png",
    }
    response = client.put('/accounts/me', headers=auth_headers(1), json=update)
    assert response.json() == {
        **get_account(1),
        **update,
    }
    assert response.status_code == 200

def test_update_display_name(client, auth_headers, get_account):
    update = {
        "display_name": "Account of Bob",
    }
    response = client.put('/accounts/me', headers=auth_headers(2), json=update)
    assert response.json() == {
        **get_account(2),
        **update,
    }

def test_update_reset_display_name(client, auth_headers, get_account):
    update = {
        "display_name": "",
    }
    response = client.put('/accounts/me', headers=auth_headers(1), json=update)
    assert response.json() == {
        **get_account(1),
        "display_name": None
    }

def test_update_password(session, client, auth_headers, get_account):
    update = {
        "username": "updated_alice",
        "old_password": "password1",
        "email": "alice2@example.com",
        "new_password": "newpassword",
    }
    mock.last_uuid = mock.OFFSETS['account'] + 100
    response = client.put('/accounts/me', headers=auth_headers(1), json=update)
    assert response.json() == {
        **get_account(1),
        "username": "updated_alice",
        # "email": "alice2@example.com" # this should not be updated immediately
    }
    assert response.status_code == 200
    # Try logging in with the new information
    response = client.post('/auth/web/login', data={
        'identifier': 'alice2@example.com',
        'password': 'newpassword'
    })
    assert response.status_code == 204
    # Make sure an EmailVerification was created
    db_account = session.get(DBAccount, mock.to_uuid(1, 'account'))
    assert db_account.email == "alice@example.com" # ensure email unchanged
    email_verification = db_account.email_verification.__dict__.copy()
    del email_verification['expires_at']
    del email_verification['_sa_instance_state']
    assert email_verification == {
        "id": mock.to_uuid(102, 'account'), # we go up 2 because we create an event
        "account_id": mock.to_uuid(1, 'account'),
        "email": "alice2@example.com",
    }

def test_update_password_incorrect(client, auth_headers, exception):
    update = {
        "old_password": "incorrect",
        "new_password": "newpassword",
    }
    response = client.put('/accounts/me', headers=auth_headers(1), json=update)
    assert response.json() == exception("invalid_credentials", "Authentication failed: invalid credentials")
    assert response.status_code == 401
    # Try logging in with the new information
    response = client.post('/auth/web/login', data={
        'identifier': 'alice@example.com',
        'password': 'newpassword'
    })
    assert response.status_code == 401

def test_update_account_username_taken(client, auth_headers, exception):
    update = {
        "username": "bob",
    }
    response = client.put('/accounts/me', headers=auth_headers(1), json=update)
    assert response.json() == exception('duplicate_entity', "Entity account with username=bob already exists")
    assert response.status_code == 422

def test_update_account_username_invalid(client, auth_headers, exception):
    update = {
        "username": "al ic e",
    }
    response = client.put('/accounts/me', headers=auth_headers(1), json=update)
    assert response.json() == exception('invalid_field', "Value 'al ic e' is invalid for field 'username'")
    assert response.status_code == 422

def test_update_account_email_taken(client, auth_headers, exception):
    update = {
        "email": "bob@example.com",
        "old_password": "password1"
    }
    response = client.put('/accounts/me', headers=auth_headers(1), json=update)
    assert response.json() == exception('duplicate_entity', "Entity account with email=bob@example.com already exists")
    assert response.status_code == 422

def test_update_account_email_invalid(client, auth_headers, exception):
    update = {
        "email": "aliceinvalidemail",
        "old_password": "password1"
    }
    response = client.put('/accounts/me', headers=auth_headers(1), json=update)
    assert response.json() == exception('invalid_field', "Value 'aliceinvalidemail' is invalid for field 'email'")
    assert response.status_code == 422

def test_delete_account(client, login, exception):
    # Log in and get access to the refresh token
    response = login(client, 1)
    refresh_token = response.cookies.get(settings.jwt_refresh_cookie_key)
    # Delete the account
    response = client.delete("/accounts/me")
    assert response.status_code == 204
    # Try accessing something
    response = client.get("/accounts/me")
    assert response.json() == exception("invalid_access_token", "Authentication failed: Access token expired or was invalid")
    assert response.status_code == 401
    # Try refreshing (cookie should have been deleted)
    response = client.post("/auth/web/refresh")
    assert response.json() == exception("not_authenticated", "Not authenticated")
    assert response.status_code == 403
    # Add the cookie and try again
    client.cookies.set(settings.jwt_refresh_cookie_key, refresh_token)
    response = client.post("/auth/web/refresh")
    assert response.json() == exception("invalid_refresh_token", "Authentication failed: Refresh token expired or was invalid")
    assert response.status_code == 401