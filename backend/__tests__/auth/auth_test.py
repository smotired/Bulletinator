"""Module for testing the authentication routes"""
from backend.database.schema import *
from backend.config import settings
from time import sleep
from datetime import datetime, UTC
from sqlalchemy import select

from backend.__tests__ import mock

def test_me_not_authenticated(client, exception):
    response = client.get("/accounts/me")
    assert response.json() == exception("not_authenticated", "Not authenticated")
    assert response.status_code == 403

def test_register_account(session, client, form_headers, exception):
    form = {
        "username": "fred",
        "email": "fred@example.com",
        "password": "password6",
    }
    mock.last_uuid = mock.OFFSETS['account'] + 100
    response = client.post("/auth/registration", headers=form_headers, data=form)
    new_user_object = {
        "id": mock.to_uuid(101, 'account'),
        "username": "fred",
        "email": None,
        "profile_image": None,
        "display_name": None
    }
    assert response.json() == new_user_object
    assert response.status_code == 201
    db_account = session.get(DBAccount, mock.to_uuid(101, 'account'))
    # Make sure a Permission was created
    permission = db_account.permission.__dict__.copy()
    del permission['_sa_instance_state']
    assert permission == {
        "id": mock.to_uuid(103, 'account'),
        "account_id": mock.to_uuid(101, 'account'),
        "role": "user",
    }
    # Make sure an EmailVerification was created
    assert db_account.email is None
    email_verification = db_account.email_verification.__dict__.copy()
    del email_verification['expires_at']
    del email_verification['_sa_instance_state']
    assert email_verification == {
        "id": mock.to_uuid(104, 'account'),
        "account_id": mock.to_uuid(101, 'account'),
        "email": "fred@example.com",
    }
    expires = db_account.email_verification.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    assert abs((expires.astimezone(UTC) - datetime.now(UTC)).total_seconds() - settings.email_verification_duration) < 5
    # Make sure we can log in even with the unverified email
    response = client.post("/auth/web/login", headers=form_headers, data={
        "identifier": "fred@example.com",
        "password": "password6"
    })
    assert response.status_code == 204
    # Make sure we CAN see our profile
    response = client.get("/accounts/me")
    assert response.json() == new_user_object
    assert response.status_code == 200
    # Make sure we can't do anything else
    response = client.put("/accounts/me", json={ "display_name": "Fred" })
    assert response.json() == exception("unverified_email_address", "This action requires a verified email address")
    assert response.status_code == 403
    # Verify the email
    response = client.post(f"/auth/verify-email/{email_verification['id']}")
    assert response.json() == { **new_user_object, "email": "fred@example.com" }
    assert response.status_code == 200
    # Make sure the verification was removed from the database
    statement = select(DBEmailVerification).where(DBEmailVerification.account_id == mock.to_uuid(101, 'account'))
    results = list( session.execute(statement).scalars().all() )
    assert len(results) == 0
    # Now make sure we can do something
    response = client.put("/accounts/me", json={ "display_name": "Fred" })
    assert response.json() == { **new_user_object, "email": "fred@example.com", "display_name": "Fred" }
    assert response.status_code == 200

def test_register_existing_username(client, form_headers, accounts, exception):
    form = {
        "username": "alice",
        "email": "alicenew@example.com",
        "password": "drowssap1",
    }
    mock.last_uuid = mock.OFFSETS['account'] + 100
    response = client.post("/auth/registration", headers=form_headers, data=form)
    assert response.json() == exception("duplicate_entity", "Entity account with username=alice already exists")
    assert response.status_code == 422

def test_register_invalid_username(client, form_headers, accounts, exception):
    form = {
        "username": "al ic e",
        "email": "alicenew@example.com",
        "password": "drowssap1",
    }
    mock.last_uuid = mock.OFFSETS['account'] + 100
    response = client.post("/auth/registration", headers=form_headers, data=form)
    assert response.json() == exception("invalid_field", "Value 'al ic e' is invalid for field 'username'")
    assert response.status_code == 422

def test_register_existing_email(client, form_headers, accounts, exception):
    form = {
        "username": "alicenew",
        "email": "alice@example.com",
        "password": "drowssap1",
    }
    mock.last_uuid = mock.OFFSETS['account'] + 100
    response = client.post("/auth/registration", headers=form_headers, data=form)
    assert response.json() == exception("duplicate_entity", "Entity account with email=alice@example.com already exists")
    assert response.status_code == 422

def test_register_invalid_email(client, form_headers, accounts, exception):
    form = {
        "username": "alicenew",
        "email": "aliceinvalidemail",
        "password": "drowssap1",
    }
    mock.last_uuid = mock.OFFSETS['account'] + 100
    response = client.post("/auth/registration", headers=form_headers, data=form)
    assert response.json() == exception('invalid_field', "Value 'aliceinvalidemail' is invalid for field 'email'")
    assert response.status_code == 422

def test_get_token(client, form_headers, create_login, get_account):
    # log in
    login = create_login(1)
    response = client.post("/auth/token", headers=form_headers, data=login)
    assert response.status_code == 200
    access_token = response.json()['access_token']
    assert response.cookies.get(settings.jwt_access_cookie_key) is None # make sure we dont make any cookies
    assert response.cookies.get(settings.jwt_refresh_cookie_key) is None
    # try an authenticated route
    response = client.get("/accounts/me", headers={ "Authorization": f"Bearer {access_token}"})
    assert response.json() == get_account(1)
    assert response.status_code == 200

def test_login(client, form_headers, create_login, get_account):
    # log in
    login = create_login(1)
    response = client.post("/auth/web/login", headers=form_headers, data=login)
    assert response.status_code == 204
    access_token = response.cookies.get(settings.jwt_access_cookie_key)
    assert access_token is not None
    refresh_token = response.cookies.get(settings.jwt_refresh_cookie_key)
    assert refresh_token is not None
    # try an authenticated route
    response = client.get("/accounts/me")
    assert response.json() == get_account(1)
    assert response.status_code == 200

def test_login_by_username(client, form_headers, get_account):
    # log in
    login = { "identifier": "alice", "password": "password1" }
    response = client.post("/auth/web/login", headers=form_headers, data=login)
    assert response.status_code == 204
    access_token = response.cookies.get(settings.jwt_access_cookie_key)
    assert access_token is not None
    refresh_token = response.cookies.get(settings.jwt_refresh_cookie_key)
    assert refresh_token is not None
    # try an authenticated route
    response = client.get("/accounts/me")
    assert response.json() == get_account(1)
    assert response.status_code == 200

def test_login_incorrect_password(client, form_headers, create_login, exception):
    login = create_login(1)
    login['password'] = "incorrect password"
    response = client.post("/auth/web/login", headers=form_headers, data=login)
    assert response.json() == exception("invalid_credentials", "Authentication failed: invalid credentials")
    assert response.status_code == 401

def test_login_nonexistent_account(client, form_headers, exception):
    login = { "identifier": "nobody@example.com", "password": "nonexistent" }
    response = client.post("/auth/web/login", headers=form_headers, data=login)
    assert response.json() == exception("invalid_credentials", "Authentication failed: invalid credentials")
    assert response.status_code == 401

def test_access_cookie_expiration(client, monkeypatch, login, exception):
    # make access tokens expire 1 minute before issuance
    monkeypatch.setattr(settings, 'jwt_access_duration', -60)
    # Log in and try accessing something
    login(client, 1)
    response = client.get("/accounts/me")
    assert response.json() == exception("invalid_access_token", "Authentication failed: Access token expired or was invalid")
    assert response.status_code == 401

def test_access_token_expiration(client, monkeypatch, auth_headers, exception):
    # make access tokens expire 1 minute before issuance
    monkeypatch.setattr(settings, 'jwt_access_duration', -60)
    # Log in and try accessing something
    response = client.get("/accounts/me", headers=auth_headers(1))
    assert response.json() == exception("invalid_access_token", "Authentication failed: Access token expired or was invalid")
    assert response.status_code == 401

def test_refresh_access_token(client, monkeypatch, login, exception, get_account):
    # make access tokens expire immediately after issuance
    monkeypatch.setattr(settings, 'jwt_access_duration', 1)
    # Log in and get access to the refresh token
    response = login(client, 1)
    # Wait 1 second and try accessing something
    sleep(2)
    response = client.get("/accounts/me")
    assert response.json() == exception("invalid_access_token", "Authentication failed: Access token expired or was invalid")
    assert response.status_code == 401
    # Refresh our token (client stores the cookies)
    response = client.post("/auth/web/refresh")
    assert response.status_code == 204
    access_token = response.cookies.get(settings.jwt_access_cookie_key)
    assert access_token is not None
    # Make sure we can use it now
    response = client.get("/accounts/me")
    assert response.json() == get_account(1)
    assert response.status_code == 200

def test_refresh_token_expiration(client, monkeypatch, login, exception):
    # make access AND refresh tokens expire 1 minute before issuance
    monkeypatch.setattr(settings, 'jwt_access_duration', -60)
    monkeypatch.setattr(settings, 'jwt_refresh_duration', -60)
    # Log in and get access to the refresh token
    response = login(client, 1)
    # Try accessing something
    response = client.get("/accounts/me")
    assert response.json() == exception("invalid_access_token", "Authentication failed: Access token expired or was invalid")
    assert response.status_code == 401
    # Try refreshing
    response = client.post("/auth/web/refresh")
    assert response.json() == exception("invalid_refresh_token", "Authentication failed: Refresh token expired or was invalid")
    assert response.status_code == 401

def test_logout(client, login):
    login(client, 1)
    response = client.post("/auth/web/logout")
    assert response.status_code == 204
    assert response.cookies.get(settings.jwt_access_cookie_key) is None
    assert response.cookies.get(settings.jwt_refresh_cookie_key) is None
    # access tokens can't actually be revoked which is why they only last 15 minutes

def test_logout_deletes_and_invalidates_refresh_token(client, monkeypatch, login, exception):
    # make access tokens expire immediately after issuance
    monkeypatch.setattr(settings, 'jwt_access_duration', 0)
    # Log in and get access to the refresh token
    response = login(client, 1)
    # Save the refresh token for later
    refresh_token = response.cookies.get(settings.jwt_refresh_cookie_key)
    # Log out
    response = client.post("/auth/web/logout")
    assert response.status_code == 204
    # Wait one second and accessing something
    sleep(1)
    response = client.get("/accounts/me")
    assert response.json() == exception("not_authenticated", "Not authenticated")
    assert response.status_code == 403
    # Try refreshing (cookie should have been deleted)
    response = client.post("/auth/web/refresh")
    assert response.json() == exception("not_authenticated", "Not authenticated")
    assert response.status_code == 403
    # Add the cookie and try again
    client.cookies.set(settings.jwt_refresh_cookie_key, refresh_token)
    response = client.post("/auth/web/refresh")
    assert response.json() == exception("invalid_refresh_token", "Authentication failed: Refresh token expired or was invalid")
    assert response.status_code == 401