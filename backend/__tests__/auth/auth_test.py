"""Module for testing the authentication routes"""
from backend.database.schema import *
from backend.config import settings

def test_view_self_when_not_authenticated(client, exception, get_user):
    user: DBUser = get_user(1)
    response = client.get("/users/me")
    assert response.json() == exception("not_authenticated", "Not authenticated")
    assert response.status_code == 403

def test_register_user(client, form_headers):
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
    assert response.json() == exception("duplicate_entity", "Entity user with username=alice already exists")
    assert response.status_code == 422

def test_register_existing_email(client, form_headers, exception):
    form = {
        "username": "alicenew",
        "email": "alice@example.com",
        "password": "drowssap1",
    }
    response = client.post("/auth/registration", headers=form_headers, data=form)
    assert response.json() == exception("duplicate_entity", "Entity user with email=alice@example.com already exists")
    assert response.status_code == 422

def test_login(client, form_headers, create_login, get_response_user):
    # log in
    login = create_login(1)
    response = client.post("/auth/login", headers=form_headers, data=login)
    access_token = response.json()
    assert response.status_code == 200
    refresh_token = response.cookies.get(settings.jwt_cookie_key)
    assert refresh_token is not None
    # create auth headers
    auth_headers = { "Authorization": f"Bearer {access_token['access_token']}" }
    # try an authenticated route
    response = client.get("/users/me", headers=auth_headers)
    assert response.json() == get_response_user(1)
    assert response.status_code == 200

def test_login_incorrect_password(client, form_headers, create_login, exception):
    login = create_login(1)
    login['password'] = "incorrect password"
    response = client.post("/auth/login", headers=form_headers, data=login)
    assert response.status_code == 401
    assert response.json() == exception("invalid_credentials", "Authentication failed: invalid username or password")

def test_login_nonexistent_user(client, form_headers, exception):
    login = { "email": "nobody@example.com", "password": "nonexistent" }
    response = client.post("/auth/login", headers=form_headers, data=login)
    assert response.status_code == 401
    assert response.json() == exception("invalid_credentials", "Authentication failed: invalid username or password")