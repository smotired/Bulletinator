"""Module for testing the authentication routes"""
from backend.database.schema import *
from backend.config import settings
from time import sleep

def test_me_not_authenticated(client, exception):
    response = client.get("/accounts/me")
    assert response.json() == exception("not_authenticated", "Not authenticated")
    assert response.status_code == 403

def test_register_account(client, form_headers):
    form = {
        "username": "fred",
        "email": "fred@example.com",
        "password": "password6",
    }
    response = client.post("/auth/registration", headers=form_headers, data=form)
    assert response.json() == {
        "id": 6,
        "username": "fred",
        "profile_image": None,
    }
    assert response.status_code == 201

def test_register_existing_username(client, form_headers, exception):
    form = {
        "username": "alice",
        "email": "alicenew@example.com",
        "password": "drowssap1",
    }
    response = client.post("/auth/registration", headers=form_headers, data=form)
    assert response.json() == exception("duplicate_entity", "Entity account with username=alice already exists")
    assert response.status_code == 422

def test_register_existing_email(client, form_headers, exception):
    form = {
        "username": "alicenew",
        "email": "alice@example.com",
        "password": "drowssap1",
    }
    response = client.post("/auth/registration", headers=form_headers, data=form)
    assert response.json() == exception("duplicate_entity", "Entity account with email=alice@example.com already exists")
    assert response.status_code == 422

def test_login(client, form_headers, create_login, get_account):
    # log in
    login = create_login(1)
    response = client.post("/auth/login", headers=form_headers, data=login)
    access_token = response.json()['access_token']
    assert response.status_code == 200
    refresh_token = response.cookies.get(settings.jwt_cookie_key)
    assert refresh_token is not None
    # create auth headers
    auth_headers = { "Authorization": f"Bearer {access_token}" }
    # try an authenticated route
    response = client.get("/accounts/me", headers=auth_headers)
    assert response.json() == get_account(1)
    assert response.status_code == 200

def test_login_incorrect_password(client, form_headers, create_login, exception):
    login = create_login(1)
    login['password'] = "incorrect password"
    response = client.post("/auth/login", headers=form_headers, data=login)
    assert response.json() == exception("invalid_credentials", "Authentication failed: invalid username or password")
    assert response.status_code == 401

def test_login_nonexistent_account(client, form_headers, exception):
    login = { "email": "nobody@example.com", "password": "nonexistent" }
    response = client.post("/auth/login", headers=form_headers, data=login)
    assert response.json() == exception("invalid_credentials", "Authentication failed: invalid username or password")
    assert response.status_code == 401

def test_access_token_expiration(client, monkeypatch, auth_headers, exception):
    # make access tokens expire 1 minute before issuance
    monkeypatch.setattr(settings, 'jwt_access_duration', -60)
    # Log in and try accessing something
    response = client.get("/accounts/me", headers=auth_headers(1))
    assert response.json() == exception("invalid_access_token", "Authentication failed: Access token expired or was invalid")
    assert response.status_code == 401

def test_refresh_access_token(client, monkeypatch, login_client, exception, get_account):
    # make access tokens expire immediately after issuance
    monkeypatch.setattr(settings, 'jwt_access_duration', 0)
    # Log in and get access to the refresh token
    auth_headers, response = login_client(client, 1)
    # Wait 1 second and try accessing something
    sleep(1)
    response = client.get("/accounts/me", headers=auth_headers)
    assert response.json() == exception("invalid_access_token", "Authentication failed: Access token expired or was invalid")
    assert response.status_code == 401
    # Refresh our token (client stores the cookies)
    response = client.post("/auth/refresh")
    assert response.status_code == 200
    access_token = response.json()['access_token']
    auth_headers = { "Authorization": f"Bearer {access_token}" }
    # Make sure we can 
    response = client.get("/accounts/me", headers=auth_headers)
    assert response.json() == get_account(1)
    assert response.status_code == 200

def test_refresh_token_expiration(client, monkeypatch, login_client, exception):
    # make access AND refresh tokens expire 1 minute before issuance
    monkeypatch.setattr(settings, 'jwt_access_duration', -60)
    monkeypatch.setattr(settings, 'jwt_refresh_duration', -60)
    # Log in and get access to the refresh token
    auth_headers, response = login_client(client, 1)
    # Try accessing something
    response = client.get("/accounts/me", headers=auth_headers)
    assert response.json() == exception("invalid_access_token", "Authentication failed: Access token expired or was invalid")
    assert response.status_code == 401
    # Try refreshing
    response = client.post("/auth/refresh")
    assert response.json() == exception("invalid_refresh_token", "Authentication failed: Refresh token expired or was invalid")
    assert response.status_code == 401

def test_logout(client, auth_headers):
    response = client.post("/auth/logout", headers=auth_headers(1))
    assert response.status_code == 204
    # access tokens can't actually be revoked which is why they only last 15 minutes

def test_logout_deletes_and_invalidates_refresh_token(client, monkeypatch, login_client, exception):
    # make access tokens expire immediately after issuance
    monkeypatch.setattr(settings, 'jwt_access_duration', 0)
    # Log in and get access to the refresh token
    auth_headers, response = login_client(client, 1)
    # Save the refresh token for later
    refresh_token = response.cookies.get(settings.jwt_cookie_key)
    # Log out
    response = client.post("/auth/logout", headers=auth_headers)
    assert response.status_code == 204
    # Wait one second and accessing something
    sleep(1)
    response = client.get("/accounts/me", headers=auth_headers)
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