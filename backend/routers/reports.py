"""Functionality for /reports routes"""

from fastapi import APIRouter, Request
from uuid import UUID

from backend.dependencies import DBSession
from backend.utils.permissions import ReportPDP
from backend.utils.rate_limiter import limit
from backend.database.schema import DBReport
from backend.database import reports as reports_db
from backend.models.reports import Report, ReportCollection, ReportCreate, ReportUpdate, StaffReportUpdate

router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)

@router.get("/", status_code=200, response_model=ReportCollection)
@limit("main")
def get_submitted(
    request: Request,
    session: DBSession, # type: ignore
    pdp: ReportPDP,
) -> list[DBReport]:
    """Returns a list of reports submitted by this user, sorted by most recent."""
    return reports_db.get_submitted(session, pdp)

@router.get("/all", status_code=200, response_model=ReportCollection)
@limit("main")
def get_reports(
    request: Request,
    session: DBSession, # type: ignore
    pdp: ReportPDP,
) -> list[DBReport]:
    """Returns a list of all reports sorted by most recent."""
    return reports_db.get_all(session, pdp)

@router.get("/assigned", status_code=200, response_model=ReportCollection)
@limit("main")
def get_assigned(
    request: Request,
    session: DBSession, # type: ignore
    pdp: ReportPDP,
) -> ReportCollection:
    """Returns a list of reports assigned to this account, sorted by most recent."""
    return reports_db.get_assigned(session, pdp)

@router.post("/", status_code=201, response_model=Report)
@limit("submit_report")
def submit_report(
    request: Request,
    session: DBSession, # type: ignore
    pdp: ReportPDP,
    config: ReportCreate,
) -> DBReport:
    """Submits and returns a report."""
    return reports_db.create_report(session, pdp, config)

@router.get("/{report_id}", status_code=200, response_model=Report)
@limit("main")
def get_report(
    request: Request,
    session: DBSession, # type: ignore
    pdp: ReportPDP,
    report_id: UUID,
) -> DBReport:
    """Finds and returns a report."""
    return reports_db.get_report(session, pdp, str(report_id))

@router.put("/{report_id}", status_code=200, response_model=Report)
@limit("main")
def update_report(
    request: Request,
    session: DBSession, # type: ignore
    pdp: ReportPDP,
    report_id: UUID,
    config: ReportUpdate,
) -> DBReport:
    """Updates and returns a report."""
    return reports_db.update_report(session, pdp, str(report_id), config)

@router.put("/{report_id}/status", status_code=200, response_model=Report)
@limit("main")
def update_status(
    request: Request,
    session: DBSession, # type: ignore
    pdp: ReportPDP,
    report_id: UUID,
    config: StaffReportUpdate,
) -> DBReport:
    """Updates and returns a report as a moderator."""
    return reports_db.update_report_status(session, pdp, str(report_id), config)

@router.delete("/{report_id}", status_code=204, response_model=None)
@limit("main", no_content=True)
def delete_report(
    request: Request,
    session: DBSession, # type: ignore
    pdp: ReportPDP,
    report_id: UUID,
) -> None:
    """Deletes a report."""
    reports_db.delete_report(session, pdp, str(report_id))

@router.put("/{report_id}/assignee/{moderator_id}", status_code=200, response_model=Report)
@limit("main")
def set_assignee(
    request: Request,
    session: DBSession, # type: ignore
    pdp: ReportPDP,
    report_id: UUID,
    moderator_id: UUID,
) -> DBReport:
    """Sets the assignee of a report."""
    return reports_db.update_assignee(session, pdp, str(report_id), str(moderator_id))

@router.delete("/{report_id}/assignee", status_code=200, response_model=Report)
@limit("main")
def remove_assignee(
    request: Request,
    session: DBSession, # type: ignore
    pdp: ReportPDP,
    report_id: UUID,
) -> DBReport:
    """Deletes an assignee from a report."""
    return reports_db.remove_assignee(session, pdp, str(report_id))