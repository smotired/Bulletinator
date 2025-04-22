"""Tests for reports"""

from backend.__tests__ import mock
from datetime import datetime, UTC

def test_submit_and_get_report(client, auth_headers, exception):
    # Submit the report
    config = {
        "entity_id": mock.to_uuid(1, 'board'), # report board 1
        "entity_type": "board",
        "report_type": "copyright_infringement",
        "report_text": "My copyrighted material appears on this board without my consent.",
    }
    mock.last_uuid = mock.OFFSETS['report']
    response = client.post("/reports/", headers=auth_headers(2), json=config)
    created_time = response.json()['created_at']
    assert (datetime.now(UTC).timestamp() - datetime.fromisoformat(created_time).timestamp()) < 2
    report = {
        **config,
        "id": mock.to_uuid(1, 'report'),
        "account_id": mock.to_uuid(2, 'account'),
        "status": "fresh",
        "moderator_id": None,
        "created_at": created_time,
        "resolved_at": None,
    }
    assert response.json() == report
    assert response.status_code == 201
    # Get it as the submitter
    response = client.get("/reports/", headers=auth_headers(2))
    assert response.json() == {
        "metadata": { "count": 1 },
        "reports": [ report ],
    }
    assert response.status_code == 200
    # Get it as a staff account
    response = client.get("/reports/all", headers=auth_headers(5))
    assert response.json() == {
        "metadata": { "count": 1 },
        "reports": [ report ],
    }
    assert response.status_code == 200
    # Assign and get as an assigned staff account
    response = client.get("/reports/assigned", headers=auth_headers(5))
    assert response.json() == {
        "metadata": { "count": 0 },
        "reports": [ ],
    }
    assert response.status_code == 200
    response = client.put(f"/reports/{mock.to_uuid(1, 'report')}/assignee/{mock.to_uuid(5, 'account')}", headers=auth_headers(5))
    report['moderator_id'] = mock.to_uuid(5, 'account')
    report['status'] = "assigned"
    assert response.json() == report
    assert response.status_code == 200
    response = client.get("/reports/assigned", headers=auth_headers(5))
    assert response.json() == {
        "metadata": { "count": 1 },
        "reports": [ report ],
    }
    assert response.status_code == 200
    # Get by ID as submitter, staff, and other
    response = client.get(f"/reports/{mock.to_uuid(1, 'report')}", headers=auth_headers(2))
    assert response.json() == report
    assert response.status_code == 200
    response = client.get(f"/reports/{mock.to_uuid(1, 'report')}", headers=auth_headers(5))
    assert response.json() == report
    assert response.status_code == 200
    response = client.get(f"/reports/{mock.to_uuid(1, 'report')}", headers=auth_headers(1))
    assert response.json() == exception("entity_not_found", f"Unable to find report with id={mock.to_uuid(1, 'report')}")
    assert response.status_code == 404

def test_get_404_report(client, auth_headers, exception):
    response = client.get(f"/reports/{mock.to_uuid(404, 'report')}", headers=auth_headers(1))
    assert response.json() == exception("entity_not_found", f"Unable to find report with id={mock.to_uuid(404, 'report')}")
    assert response.status_code == 404

def test_update_report(client, auth_headers):
    # Submit the report
    config = {
        "entity_id": mock.to_uuid(1, 'board'), # report board 1
        "entity_type": "board",
        "report_type": "copyright_infringement",
        "report_text": "My copyrighted material appears on this board without my consent.",
    }
    mock.last_uuid = mock.OFFSETS['report']
    response = client.post("/reports/", headers=auth_headers(2), json=config)
    created_time = response.json()['created_at']
    assert (datetime.now(UTC).timestamp() - datetime.fromisoformat(created_time).timestamp()) < 2
    report = {
        **config,
        "id": mock.to_uuid(1, 'report'),
        "account_id": mock.to_uuid(2, 'account'),
        "status": "fresh",
        "moderator_id": None,
        "created_at": created_time,
        "resolved_at": None,
    }
    assert response.json() == report
    assert response.status_code == 201
    # Update text
    update = { "report_text": "Please fix immediately." }
    response = client.put(f"/reports/{mock.to_uuid(1, 'report')}", headers=auth_headers(2), json=update)
    assert response.json() == {
        **report,
        **update
    }
    assert response.status_code == 200

def test_update_404_report(client, auth_headers, exception):
    update = { "report_text": "missing report update" }
    response = client.put(f"/reports/{mock.to_uuid(404, 'report')}", headers=auth_headers(1), json=update)
    assert response.json() == exception("entity_not_found", f"Unable to find report with id={mock.to_uuid(404, 'report')}")
    assert response.status_code == 404

def test_update_404_report_status(client, auth_headers, exception):
    update = { "status": "resolved" }
    response = client.put(f"/reports/{mock.to_uuid(404, 'report')}/status", headers=auth_headers(5), json=update)
    assert response.json() == exception("entity_not_found", f"Unable to find report with id={mock.to_uuid(404, 'report')}")
    assert response.status_code == 404

def test_update_report_as_other_account(client, auth_headers, exception):
    """Should return a 404"""
    # Submit the report
    config = {
        "entity_id": mock.to_uuid(1, 'board'), # report board 1
        "entity_type": "board",
        "report_type": "copyright_infringement",
        "report_text": "My copyrighted material appears on this board without my consent.",
    }
    mock.last_uuid = mock.OFFSETS['report']
    response = client.post("/reports/", headers=auth_headers(2), json=config)
    created_time = response.json()['created_at']
    assert (datetime.now(UTC).timestamp() - datetime.fromisoformat(created_time).timestamp()) < 2
    report = {
        **config,
        "id": mock.to_uuid(1, 'report'),
        "account_id": mock.to_uuid(2, 'account'),
        "status": "fresh",
        "moderator_id": None,
        "created_at": created_time,
        "resolved_at": None,
    }
    assert response.json() == report
    assert response.status_code == 201
    # Update text
    update = { "report_text": "Please fix immediately." }
    response = client.put(f"/reports/{mock.to_uuid(1, 'report')}", headers=auth_headers(1), json=update)
    assert response.json() == exception("entity_not_found", f"Unable to find report with id={mock.to_uuid(1, 'report')}")
    assert response.status_code == 404

def test_update_report_as_assignee(client, auth_headers, exception):
    """Only the submitter should be able to modify report text."""
    # Submit the report
    config = {
        "entity_id": mock.to_uuid(1, 'board'), # report board 1
        "entity_type": "board",
        "report_type": "copyright_infringement",
        "report_text": "My copyrighted material appears on this board without my consent.",
    }
    mock.last_uuid = mock.OFFSETS['report']
    response = client.post("/reports/", headers=auth_headers(2), json=config)
    created_time = response.json()['created_at']
    assert (datetime.now(UTC).timestamp() - datetime.fromisoformat(created_time).timestamp()) < 2
    report = {
        **config,
        "id": mock.to_uuid(1, 'report'),
        "account_id": mock.to_uuid(2, 'account'),
        "status": "fresh",
        "moderator_id": None,
        "created_at": created_time,
        "resolved_at": None,
    }
    assert response.json() == report
    assert response.status_code == 201
    # Assign moderator
    response = client.put(f"/reports/{mock.to_uuid(1, 'report')}/assignee/{mock.to_uuid(5, 'account')}", headers=auth_headers(5))
    assert response.status_code == 200
    # Update text
    update = { "report_text": "Will be fixed" }
    response = client.put(f"/reports/{mock.to_uuid(1, 'report')}", headers=auth_headers(5), json=update)
    assert response.json() == exception("no_permissions", f"No permissions to update report on report with id={mock.to_uuid(1, 'report')}")
    assert response.status_code == 403

def test_update_report_status(client, auth_headers):
    # Submit the report
    config = {
        "entity_id": mock.to_uuid(1, 'board'), # report board 1
        "entity_type": "board",
        "report_type": "copyright_infringement",
        "report_text": "My copyrighted material appears on this board without my consent.",
    }
    mock.last_uuid = mock.OFFSETS['report']
    response = client.post("/reports/", headers=auth_headers(2), json=config)
    created_time = response.json()['created_at']
    assert (datetime.now(UTC).timestamp() - datetime.fromisoformat(created_time).timestamp()) < 2
    report = {
        **config,
        "id": mock.to_uuid(1, 'report'),
        "account_id": mock.to_uuid(2, 'account'),
        "status": "fresh",
        "moderator_id": None,
        "created_at": created_time,
        "resolved_at": None,
    }
    assert response.json() == report
    assert response.status_code == 201
    # Assign moderator
    response = client.put(f"/reports/{mock.to_uuid(1, 'report')}/assignee/{mock.to_uuid(5, 'account')}", headers=auth_headers(5))
    assert response.status_code == 200
    # Update status
    update = { "status": "resolved" }
    response = client.put(f"/reports/{mock.to_uuid(1, 'report')}/status", headers=auth_headers(5), json=update)
    resolved_at = response.json()['resolved_at']
    assert resolved_at is not None
    assert response.json() == {
        **report,
        **update,
        "moderator_id": mock.to_uuid(5, 'account'),
        "resolved_at": resolved_at,
    }
    assert response.status_code == 200
    # Update status to unresolved
    update = { "status": "in_progress" }
    response = client.put(f"/reports/{mock.to_uuid(1, 'report')}/status", headers=auth_headers(5), json=update)
    assert response.json() == {
        **report,
        **update,
        "moderator_id": mock.to_uuid(5, 'account'),
        "resolved_at": None,
    }
    assert response.status_code == 200

def test_update_report_status_as_submitter(client, auth_headers, exception):
    """Only assigned staff member should be able to do this."""
    # Submit the report
    config = {
        "entity_id": mock.to_uuid(1, 'board'), # report board 1
        "entity_type": "board",
        "report_type": "copyright_infringement",
        "report_text": "My copyrighted material appears on this board without my consent.",
    }
    mock.last_uuid = mock.OFFSETS['report']
    response = client.post("/reports/", headers=auth_headers(2), json=config)
    created_time = response.json()['created_at']
    assert (datetime.now(UTC).timestamp() - datetime.fromisoformat(created_time).timestamp()) < 2
    report = {
        **config,
        "id": mock.to_uuid(1, 'report'),
        "account_id": mock.to_uuid(2, 'account'),
        "status": "fresh",
        "moderator_id": None,
        "created_at": created_time,
        "resolved_at": None,
    }
    assert response.json() == report
    assert response.status_code == 201
    # Update text
    update = { "status": "resolved" }
    response = client.put(f"/reports/{mock.to_uuid(1, 'report')}/status", headers=auth_headers(2), json=update)
    assert response.json() == exception("no_permissions", f"No permissions to update report status on report with id={mock.to_uuid(1, 'report')}")
    assert response.status_code == 403

def test_delete_report(client, auth_headers, exception):
    # Submit the report
    config = {
        "entity_id": mock.to_uuid(1, 'board'), # report board 1
        "entity_type": "board",
        "report_type": "copyright_infringement",
        "report_text": "My copyrighted material appears on this board without my consent.",
    }
    mock.last_uuid = mock.OFFSETS['report']
    response = client.post("/reports/", headers=auth_headers(2), json=config)
    created_time = response.json()['created_at']
    assert (datetime.now(UTC).timestamp() - datetime.fromisoformat(created_time).timestamp()) < 2
    report = {
        **config,
        "id": mock.to_uuid(1, 'report'),
        "account_id": mock.to_uuid(2, 'account'),
        "status": "fresh",
        "moderator_id": None,
        "created_at": created_time,
        "resolved_at": None,
    }
    assert response.json() == report
    assert response.status_code == 201
    # Delete
    response = client.delete(f"/reports/{mock.to_uuid(1, 'report')}", headers=auth_headers(2))
    assert response.status_code == 204
    # Make sure it's gone
    response = client.get(f"/reports/{mock.to_uuid(1, 'report')}", headers=auth_headers(2))
    assert response.json() == exception("entity_not_found", f"Unable to find report with id={mock.to_uuid(1, 'report')}")
    assert response.status_code == 404

def test_delete_404_report(client, auth_headers, exception):
    response = client.delete(f"/reports/{mock.to_uuid(404, 'report')}", headers=auth_headers(1))
    assert response.json() == exception("entity_not_found", f"Unable to find report with id={mock.to_uuid(404, 'report')}")
    assert response.status_code == 404

def test_delete_report_as_account(client, auth_headers, exception):
    """Should return a 404"""
    # Submit the report
    config = {
        "entity_id": mock.to_uuid(1, 'board'), # report board 1
        "entity_type": "board",
        "report_type": "copyright_infringement",
        "report_text": "My copyrighted material appears on this board without my consent.",
    }
    mock.last_uuid = mock.OFFSETS['report']
    response = client.post("/reports/", headers=auth_headers(2), json=config)
    created_time = response.json()['created_at']
    assert (datetime.now(UTC).timestamp() - datetime.fromisoformat(created_time).timestamp()) < 2
    report = {
        **config,
        "id": mock.to_uuid(1, 'report'),
        "account_id": mock.to_uuid(2, 'account'),
        "status": "fresh",
        "moderator_id": None,
        "created_at": created_time,
        "resolved_at": None,
    }
    assert response.json() == report
    assert response.status_code == 201
    # Delete
    response = client.delete(f"/reports/{mock.to_uuid(1, 'report')}", headers=auth_headers(1))
    assert response.json() == exception("entity_not_found", f"Unable to find report with id={mock.to_uuid(1, 'report')}")
    assert response.status_code == 404

def test_delete_report_as_staff(client, auth_headers, exception):
    # Submit the report
    config = {
        "entity_id": mock.to_uuid(1, 'board'), # report board 1
        "entity_type": "board",
        "report_type": "copyright_infringement",
        "report_text": "My copyrighted material appears on this board without my consent.",
    }
    mock.last_uuid = mock.OFFSETS['report']
    response = client.post("/reports/", headers=auth_headers(2), json=config)
    created_time = response.json()['created_at']
    assert (datetime.now(UTC).timestamp() - datetime.fromisoformat(created_time).timestamp()) < 2
    report = {
        **config,
        "id": mock.to_uuid(1, 'report'),
        "account_id": mock.to_uuid(2, 'account'),
        "status": "fresh",
        "moderator_id": None,
        "created_at": created_time,
        "resolved_at": None,
    }
    assert response.json() == report
    assert response.status_code == 201
    # Delete
    response = client.delete(f"/reports/{mock.to_uuid(1, 'report')}", headers=auth_headers(5))
    assert response.status_code == 204
    # Make sure it's gone
    response = client.get(f"/reports/{mock.to_uuid(1, 'report')}", headers=auth_headers(2))
    assert response.json() == exception("entity_not_found", f"Unable to find report with id={mock.to_uuid(1, 'report')}")
    assert response.status_code == 404

def test_assign_report(client, auth_headers):
    # Submit the report
    config = {
        "entity_id": mock.to_uuid(1, 'board'), # report board 1
        "entity_type": "board",
        "report_type": "copyright_infringement",
        "report_text": "My copyrighted material appears on this board without my consent.",
    }
    mock.last_uuid = mock.OFFSETS['report']
    response = client.post("/reports/", headers=auth_headers(2), json=config)
    created_time = response.json()['created_at']
    assert (datetime.now(UTC).timestamp() - datetime.fromisoformat(created_time).timestamp()) < 2
    report = {
        **config,
        "id": mock.to_uuid(1, 'report'),
        "account_id": mock.to_uuid(2, 'account'),
        "status": "fresh",
        "moderator_id": None,
        "created_at": created_time,
        "resolved_at": None,
    }
    assert response.json() == report
    assert response.status_code == 201
    # Assign moderator
    response = client.put(f"/reports/{mock.to_uuid(1, 'report')}/assignee/{mock.to_uuid(5, 'account')}", headers=auth_headers(5))
    assert response.json() == {
        **report,
        "moderator_id": mock.to_uuid(5, 'account'),
        "status": "assigned",
    }
    assert response.status_code == 200

def test_assign_to_non_staff(client, auth_headers, exception):
    # Submit the report
    config = {
        "entity_id": mock.to_uuid(1, 'board'), # report board 1
        "entity_type": "board",
        "report_type": "copyright_infringement",
        "report_text": "My copyrighted material appears on this board without my consent.",
    }
    mock.last_uuid = mock.OFFSETS['report']
    response = client.post("/reports/", headers=auth_headers(2), json=config)
    created_time = response.json()['created_at']
    assert (datetime.now(UTC).timestamp() - datetime.fromisoformat(created_time).timestamp()) < 2
    report = {
        **config,
        "id": mock.to_uuid(1, 'report'),
        "account_id": mock.to_uuid(2, 'account'),
        "status": "fresh",
        "moderator_id": None,
        "created_at": created_time,
        "resolved_at": None,
    }
    assert response.json() == report
    assert response.status_code == 201
    # Assign moderator
    response = client.put(f"/reports/{mock.to_uuid(1, 'report')}/assignee/{mock.to_uuid(1, 'account')}", headers=auth_headers(5))
    assert response.json() == exception("no_permissions", f"No permissions to become assignee on report with id={mock.to_uuid(1, 'report')}")
    assert response.status_code == 403

def test_assign_as_non_staff(client, auth_headers, exception):
    # Submit the report
    config = {
        "entity_id": mock.to_uuid(1, 'board'), # report board 1
        "entity_type": "board",
        "report_type": "copyright_infringement",
        "report_text": "My copyrighted material appears on this board without my consent.",
    }
    mock.last_uuid = mock.OFFSETS['report']
    response = client.post("/reports/", headers=auth_headers(2), json=config)
    created_time = response.json()['created_at']
    assert (datetime.now(UTC).timestamp() - datetime.fromisoformat(created_time).timestamp()) < 2
    report = {
        **config,
        "id": mock.to_uuid(1, 'report'),
        "account_id": mock.to_uuid(2, 'account'),
        "status": "fresh",
        "moderator_id": None,
        "created_at": created_time,
        "resolved_at": None,
    }
    assert response.json() == report
    assert response.status_code == 201
    # Assign moderator
    response = client.put(f"/reports/{mock.to_uuid(1, 'report')}/assignee/{mock.to_uuid(5, 'account')}", headers=auth_headers(2))
    assert response.json() == exception("no_permissions", f"No permissions to manage assignee on report with id={mock.to_uuid(1, 'report')}")
    assert response.status_code == 403

def test_unassign_report(client, auth_headers):
    # Submit the report
    config = {
        "entity_id": mock.to_uuid(1, 'board'), # report board 1
        "entity_type": "board",
        "report_type": "copyright_infringement",
        "report_text": "My copyrighted material appears on this board without my consent.",
    }
    mock.last_uuid = mock.OFFSETS['report']
    response = client.post("/reports/", headers=auth_headers(2), json=config)
    created_time = response.json()['created_at']
    assert (datetime.now(UTC).timestamp() - datetime.fromisoformat(created_time).timestamp()) < 2
    report = {
        **config,
        "id": mock.to_uuid(1, 'report'),
        "account_id": mock.to_uuid(2, 'account'),
        "status": "fresh",
        "moderator_id": None,
        "created_at": created_time,
        "resolved_at": None,
    }
    assert response.json() == report
    assert response.status_code == 201
    # Assign moderator
    response = client.put(f"/reports/{mock.to_uuid(1, 'report')}/assignee/{mock.to_uuid(5, 'account')}", headers=auth_headers(5))
    assert response.json() == {
        **report,
        "moderator_id": mock.to_uuid(5, 'account'),
        "status": "assigned",
    }
    assert response.status_code == 200
    # Unassign moderator
    response = client.delete(f"/reports/{mock.to_uuid(1, 'report')}/assignee", headers=auth_headers(5))
    assert response.json() == {
        **report,
        "moderator_id": None,
        "status": "fresh",
    }
    assert response.status_code == 200

def test_unassign_unassigned_report(client, auth_headers):
    # Submit the report
    config = {
        "entity_id": mock.to_uuid(1, 'board'), # report board 1
        "entity_type": "board",
        "report_type": "copyright_infringement",
        "report_text": "My copyrighted material appears on this board without my consent.",
    }
    mock.last_uuid = mock.OFFSETS['report']
    response = client.post("/reports/", headers=auth_headers(2), json=config)
    created_time = response.json()['created_at']
    assert (datetime.now(UTC).timestamp() - datetime.fromisoformat(created_time).timestamp()) < 2
    report = {
        **config,
        "id": mock.to_uuid(1, 'report'),
        "account_id": mock.to_uuid(2, 'account'),
        "status": "fresh",
        "moderator_id": None,
        "created_at": created_time,
        "resolved_at": None,
    }
    assert response.json() == report
    assert response.status_code == 201
    # Unassign moderator
    response = client.delete(f"/reports/{mock.to_uuid(1, 'report')}/assignee", headers=auth_headers(5))
    assert response.json() == {
        **report,
        "moderator_id": None,
        "status": "fresh",
    }
    assert response.status_code == 200

def test_unassign_as_non_staff(client, auth_headers, exception):
    # Submit the report
    config = {
        "entity_id": mock.to_uuid(1, 'board'), # report board 1
        "entity_type": "board",
        "report_type": "copyright_infringement",
        "report_text": "My copyrighted material appears on this board without my consent.",
    }
    mock.last_uuid = mock.OFFSETS['report']
    response = client.post("/reports/", headers=auth_headers(2), json=config)
    created_time = response.json()['created_at']
    assert (datetime.now(UTC).timestamp() - datetime.fromisoformat(created_time).timestamp()) < 2
    report = {
        **config,
        "id": mock.to_uuid(1, 'report'),
        "account_id": mock.to_uuid(2, 'account'),
        "status": "fresh",
        "moderator_id": None,
        "created_at": created_time,
        "resolved_at": None,
    }
    assert response.json() == report
    assert response.status_code == 201
    # Assign moderator
    response = client.delete(f"/reports/{mock.to_uuid(1, 'report')}/assignee", headers=auth_headers(2))
    assert response.json() == exception("no_permissions", f"No permissions to manage assignee on report with id={mock.to_uuid(1, 'report')}")
    assert response.status_code == 403