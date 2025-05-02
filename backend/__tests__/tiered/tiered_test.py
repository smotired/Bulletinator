"""Tests related to restricting features to free-tier users."""

from backend.config import settings
from backend.__tests__ import mock
from backend.database.schema import DBCustomer

def test_create_premium_item(client, auth_headers, items, exception):
    config = { "type": "document", "title": "Created Document" }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=config)
    assert response.json() == exception("premium_feature", "This feature is exclusive to Premium users. Please upgrade your subscription.")
    assert response.status_code == 403

def test_update_premium_item(session, client, auth_headers, items, exception):
    # Create a Document item
    customer = session.get(DBCustomer, mock.to_uuid(1, 'customer'))
    customer.type = "active"
    session.add(customer)
    session.commit()
    config = { "type": "document", "title": "Created Document" }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(1), json=config)
    assert response.status_code == 201
    # Remove their subscription and try updating it
    customer.type = "free"
    session.add(customer)
    session.commit()
    config = { "title": "Updated Document" }
    response = client.put(f"/boards/{mock.to_uuid(1, 'board')}/items/{mock.to_uuid(len(items) + 1, 'item')}", headers=auth_headers(1), json=config)
    assert response.json() == exception("premium_feature", "This feature is exclusive to Premium users. Please upgrade your subscription.")
    assert response.status_code == 403

def test_create_item_over_limit(monkeypatch, client, auth_headers, items, exception):
    # Set the item limit to 1 as account 2 has exactly one item
    monkeypatch.setattr(settings, "free_tier_item_limit", 1)
    # Try creating an item
    config = { "type": "note", "text": "Created Note" }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(3, 'board')}/items", headers=auth_headers(2), json=config)
    assert response.json() == exception("item_limit_exceeded", "You have exceeded your item creation limit. Please delete items or upgrade your subscription.")
    assert response.status_code == 403

def test_create_premium_item_owner_authoritative_negative(session, client, auth_headers, items, exception):
    # Give account 2 premium, but board 1's permissions should still depend on the owner, account 1
    customer = session.get(DBCustomer, mock.to_uuid(2, 'customer'))
    customer.type = "active"
    session.add(customer)
    session.commit()
    # Make the request
    config = { "type": "document", "title": "Created Document" }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(2), json=config)
    assert response.json() == exception("premium_feature", "This feature is exclusive to Premium users. Please upgrade your subscription.")
    assert response.status_code == 403

def test_update_premium_item_owner_authoritative_negative(session, client, auth_headers, items, exception):
    # Give account 2 premium, but board 1's permissions should still depend on the owner, account 1
    customer = session.get(DBCustomer, mock.to_uuid(2, 'customer'))
    customer.type = "active"
    session.add(customer)
    session.commit()
    # Create a Document item
    customer = session.get(DBCustomer, mock.to_uuid(1, 'customer'))
    customer.type = "active"
    session.add(customer)
    session.commit()
    config = { "type": "document", "title": "Created Document" }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(2), json=config)
    assert response.status_code == 201
    # Remove their subscription and try updating it
    customer.type = "free"
    session.add(customer)
    session.commit()
    config = { "title": "Updated Document" }
    response = client.put(f"/boards/{mock.to_uuid(1, 'board')}/items/{mock.to_uuid(len(items) + 1, 'item')}", headers=auth_headers(2), json=config)
    assert response.json() == exception("premium_feature", "This feature is exclusive to Premium users. Please upgrade your subscription.")
    assert response.status_code == 403

def test_create_item_over_limit_owner_authoritative_negative(session, monkeypatch, client, auth_headers, items, exception):
    # Set the item limit to 5
    monkeypatch.setattr(settings, "free_tier_item_limit", 5)
    # Give account 2 premium, but board 1's permissions should still depend on the owner, account 1
    customer = session.get(DBCustomer, mock.to_uuid(2, 'customer'))
    customer.type = "active"
    session.add(customer)
    session.commit()
    # Try creating an item
    config = { "type": "note", "text": "Created Note" }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(2), json=config)
    assert response.json() == exception("item_limit_exceeded", "You have exceeded your item creation limit. Please delete items or upgrade your subscription.")
    assert response.status_code == 403

def test_create_premium_item_owner_authoritative_positive(session, client, auth_headers, items, def_item):
    # Give account 1 premium, and not 2, but make sure account 2 can still use premium features on a board owned by account 1.
    customer = session.get(DBCustomer, mock.to_uuid(1, 'customer'))
    customer.type = "active"
    session.add(customer)
    session.commit()
    # Make the request
    config = { "type": "document", "title": "Created Document" }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(2), json=config)
    assert response.json() == {
        **def_item(1),
        **config,
        "text": "",
    }
    assert response.status_code == 201

def test_update_premium_item_owner_authoritative_positive(session, client, auth_headers, items, def_item):
    # Give account 1 premium, and not 2, but make sure account 2 can still use premium features on a board owned by account 1.
    customer = session.get(DBCustomer, mock.to_uuid(1, 'customer'))
    customer.type = "active"
    session.add(customer)
    session.commit()
    # Create a Document item
    config = { "type": "document", "title": "Created Document" }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(2), json=config)
    assert response.status_code == 201
    # Update it
    update = { "title": "Updated Document" }
    response = client.put(f"/boards/{mock.to_uuid(1, 'board')}/items/{mock.to_uuid(len(items) + 1, 'item')}", headers=auth_headers(2), json=update)
    assert response.json() == {
        **def_item(1),
        **config,
        **update,
        "text": "",
    }
    assert response.status_code == 200

def test_create_item_over_limit_owner_authoritative_positive(session, monkeypatch, client, auth_headers, items, def_item):
    # Set the item limit to 1 which account 2 is definitely over
    monkeypatch.setattr(settings, "free_tier_item_limit", 1)
    # Give account 1 premium, and not 2, but make sure account 2 can still use premium features on a board owned by account 1.
    customer = session.get(DBCustomer, mock.to_uuid(1, 'customer'))
    customer.type = "active"
    session.add(customer)
    session.commit()
    # Try creating an item
    config = { "type": "note", "text": "Created Note" }
    mock.last_uuid = mock.OFFSETS['item'] + len(items)
    response = client.post(f"/boards/{mock.to_uuid(1, 'board')}/items", headers=auth_headers(2), json=config)
    assert response.json() == {
        **def_item(1),
        **config,
    }
    assert response.status_code == 201