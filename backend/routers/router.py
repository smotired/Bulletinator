"""Functionality for /reports routes"""

from fastapi import APIRouter
from uuid import UUID

from backend.dependencies import DBSession
from backend.utils.permissions import ReportPDP
from backend.database.schema import DBReport
from backend.database import reports as reports_db
from backend.models.reports import Report, ReportCollection, ReportCreate, ReportUpdate, StaffReportUpdate
from backend.models.shared import Metadata

router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)

@router.get("/", status_code=200, response_model=ReportCollection)
def get_submitted(
    session: DBSession, # type: ignore
    pdp: ReportPDP,
) -> ReportCollection:
    """Returns a list of reports submitted by this user, sorted by most recent."""
    reports: list[DBReport] = reports_db.get_submitted(session, pdp)
    return ReportCollection(
        metadata=Metadata(count=len(reports)),
        reports=reports
    )

@router.get("/all", status_code=200, response_model=ReportCollection)
def get_reports(
    session: DBSession, # type: ignore
    pdp: ReportPDP,
) -> ReportCollection:
    """Returns a list of all reports sorted by most recent."""
    reports: list[DBReport] = reports_db.get_all(session, pdp)
    return ReportCollection(
        metadata=Metadata(count=len(reports)),
        reports=reports
    )

@router.get("/assigned", status_code=200, response_model=ReportCollection)
def get_assigned(
    session: DBSession, # type: ignore
    pdp: ReportPDP,
) -> ReportCollection:
    """Returns a list of reports assigned to this account, sorted by most recent."""
    reports: list[DBReport] = reports_db.get_assigned(session, pdp)
    return ReportCollection(
        metadata=Metadata(count=len(reports)),
        reports=reports
    )

@router.post("/", status_code=201, response_model=Report)
def submit_report(
    session: DBSession, # type: ignore
    pdp: ReportPDP,
    config: ReportCreate,
) -> DBReport:
    """Submits and returns a report."""
    return reports_db.create_report(session, pdp, config)

@router.put("/{report_id}", status_code=200, response_model=Report)
def update_report(
    session: DBSession, # type: ignore
    pdp: ReportPDP,
    report_id: UUID,
    config: ReportUpdate,
) -> DBReport:
    """Updates and returns a report."""
    return reports_db.update_report(session, pdp, str(report_id), config)

@router.put("/{report_id}/status", status_code=200, response_model=Report)
def update_status(
    session: DBSession, # type: ignore
    pdp: ReportPDP,
    report_id: UUID,
    config: StaffReportUpdate,
) -> DBReport:
    """Updates and returns a report as a moderator."""
    return reports_db.update_report_status(session, pdp, str(report_id), config)

@router.delete("/", status_code=204, response_model=None)
def delete_report(
    session: DBSession, # type: ignore
    pdp: ReportPDP,
    report_id: UUID,
) -> None:
    """Deletes a report."""
    reports_db.delete_report(session, pdp, str(report_id))

@router.put("/{report_id}/assignee/{moderator_id}", status_code=200, response_model=Report)
def set_assignee(
    session: DBSession, # type: ignore
    pdp: ReportPDP,
    report_id: UUID,
    moderator_id: UUID,
) -> DBReport:
    """Sets the assignee of a report."""
    return reports_db.update_assignee(session, pdp, str(report_id), str(moderator_id))

@router.delete("/{report_id}/assignee", status_code=200, response_model=Report)
def remove_assignee(
    session: DBSession, # type: ignore
    pdp: ReportPDP,
    report_id: UUID,
) -> DBReport:
    """Deletes an assignee from a report."""
    return reports_db.remove_assignee(session, pdp, str(report_id))