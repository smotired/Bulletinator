"""Tests for managing accounts"""

from backend.config import settings

def test_get_users(client, get_response_user):
    response = client.get("/users")
    assert response.json() == {
        "metadata": { "count": 5, },
        "users": [ get_response_user(1), get_response_user(2), get_response_user(3), get_response_user(4), get_response_user(5) ]
    }
    assert response.status_code == 200

def test_get_user(client, get_response_user):
    response = client.get("/users/1")
    assert response.json() == get_response_user(1)
    assert response.status_code == 200

# No tests for creating accounts because that's handled in registrating

def test_update_user(client, auth_headers, get_user):
    update = {
        "username": "updated_alice",
        "profile_image": "/static/images/test_image.png",
    }
    response = client.put('/users/me', headers=auth_headers(1), json=update)
    assert response.json() == {
        **get_user(1),
        **update,
    }
    assert response.status_code == 200

def test_update_password(client, auth_headers, get_user):
    update = {
        "username": "updated_alice",
        "old_password": "password1",
        "email": "alice2@example.com",
        "new_password": "newpassword",
    }
    response = client.put('/users/me', headers=auth_headers(1), json=update)
    assert response.json() == {
        **get_user(1),
        "username": "updated_alice",
        "email": "alice2@example.com"
    }
    assert response.status_code == 200
    # Try logging in with the new information
    response = client.post('/auth/login', data={
        'email': 'alice2@example.com',
        'password': 'newpassword'
    })
    assert response.status_code == 200

def test_update_password_incorrect(client, auth_headers, exception):
    update = {
        "old_password": "incorrect",
        "new_password": "newpassword",
    }
    response = client.put('/users/me', headers=auth_headers(1), json=update)
    assert response.json() == exception("invalid_credentials", "Authentication failed: invalid username or password")
    assert response.status_code == 401
    # Try logging in with the new information
    response = client.post('/auth/login', data={
        'email': 'alice@example.com',
        'password': 'newpassword'
    })
    assert response.status_code == 401

def test_update_user_username_taken(client, auth_headers, exception):
    update = {
        "username": "bob",
    }
    response = client.put('/users/me', headers=auth_headers(1), json=update)
    assert response.json() == exception('duplicate_entity', "Entity user with username=bob already exists")
    assert response.status_code == 422

def test_update_user_email_taken(client, auth_headers, exception):
    update = {
        "email": "bob@example.com",
        "old_password": "password1"
    }
    response = client.put('/users/me', headers=auth_headers(1), json=update)
    assert response.json() == exception('duplicate_entity', "Entity user with email=bob@example.com already exists")
    assert response.status_code == 422

def test_delete_account(client, login_client, exception):
    # Log in and get access to the refresh token
    auth_headers, response = login_client(client, 1)
    refresh_token = response.cookies.get(settings.jwt_cookie_key)
    # Delete the account
    response = client.delete("/users/me", headers=auth_headers)
    assert response.status_code == 204
    # Try accessing something
    response = client.get("/users/me", headers=auth_headers)
    assert response.json() == exception("invalid_access_token", "Authentication failed: Access token expired or was invalid")
    assert response.status_code == 401
    # Try refreshing (cookie should have been deleted)
    response = client.post("/auth/refresh")
    assert response.json() == exception("not_authenticated", "Not authenticated")
    assert response.status_code == 403
    # Add the cookie and try again
    client.cookies.set(settings.jwt_cookie_key, refresh_token)
    response = client.post("/auth/refresh")
    assert response.json() == exception("invalid_refresh_token", "Authentication failed: Refresh token expired or was invalid")
    assert response.status_code == 401