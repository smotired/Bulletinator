"""Database functions for user reports"""

from sqlalchemy import select
from datetime import datetime, UTC

from backend.dependencies import DBSession
from backend.utils.permissions import ReportPolicyDecisionPoint
from backend.database import accounts as accounts_db
from backend.database.schema import DBAccount, DBPermission, DBReport
from backend.models.reports import ReportCreate, ReportUpdate, StaffReportUpdate
from backend.exceptions import *

def get_by_id(
    session: DBSession, # type: ignore
    report_id: str,
) -> DBReport:
    """Gets a report by ID or raises a 404 if it doesn't exists."""
    report: DBReport | None = session.get(DBReport, report_id)
    if report is None:
        raise EntityNotFound('report', 'id', report_id)
    return report

def get_all(
    session: DBSession, # type: ignore
    pdp: ReportPolicyDecisionPoint,
) -> list[DBReport]:
    """Gets a list of all user reports"""
    pdp.ensure_read_all()
    statement = select(DBReport)
    results = list( session.execute(statement).scalars().all() )
    return results

def get_submitted(
    session: DBSession, # type: ignore
    pdp: ReportPolicyDecisionPoint,
) -> list[DBReport]:
    """Gets a list of reports submitted by this user"""
    pdp.ensure_query_all()
    statement = select(DBReport).where(DBReport.account_id == pdp.account.id)
    results = list( session.execute(statement).scalars().all() )
    return results

def get_assigned(
    session: DBSession, # type: ignore
    pdp: ReportPolicyDecisionPoint,
) -> list[DBReport]:
    """Gets a list of reports assigned to this user"""
    pdp.ensure_query_all()
    statement = select(DBReport).where(DBReport.moderator_id == pdp.account.id)
    results = list( session.execute(statement).scalars().all() )
    return results

def get_report(
    session: DBSession, # type: ignore
    pdp: ReportPolicyDecisionPoint,
    report_id: str,
) -> DBReport:
    """Gets a specific report by ID"""
    report: DBReport = get_by_id(session, report_id)
    pdp.ensure_read(report_id)
    return report

def create_report(
    session: DBSession, # type: ignore
    pdp: ReportPolicyDecisionPoint,
    config: ReportCreate,
) -> DBReport:
    """Creates and returns a report."""
    pdp.ensure_create()
    report = DBReport(
        account_id=pdp.account.id,
        **config.model_dump(),
    )
    session.add(report)
    session.commit()
    session.refresh(report)
    return report

def update_report(
    session: DBSession, # type: ignore
    pdp: ReportPolicyDecisionPoint,
    report_id: str,
    config: ReportUpdate,
) -> DBReport:
    """Updates and returns a report."""
    report: DBReport = get_by_id(session, report_id)
    pdp.ensure_update(report_id)
    if config.report_text is not None:
        report.report_text = config.report_text
    session.add(report)
    session.commit()
    session.refresh(report)
    return report

def update_report_status(
    session: DBSession, # type: ignore
    pdp: ReportPolicyDecisionPoint,
    report_id: str,
    config: StaffReportUpdate,
) -> DBReport:
    """Updates and returns a report."""
    report: DBReport = get_by_id(session, report_id)
    pdp.ensure_update_status(report_id)
    # Update both status and resolve time
    if config.status is not None and config.status != report.status: # status updates have changes so we only do stuff if it's changed
        report.status = config.status
        if config.status == "resolved":
            report.resolved_at = datetime.now(UTC)
        else:
            report.resolved_at = None
    session.add(report)
    session.commit()
    session.refresh(report)
    return report

def delete_report(
    session: DBSession, # type: ignore
    pdp: ReportPolicyDecisionPoint,
    report_id: str,
) -> None:
    """Deletes a report."""
    report: DBReport = get_by_id(session, report_id)
    pdp.ensure_delete(report_id)
    session.delete(report)
    session.commit()

def update_assignee(
    session: DBSession, # type: ignore
    pdp: ReportPolicyDecisionPoint,
    report_id: str,
    assignee_id: str,
) -> DBReport:
    """Updates assignee and returns a report."""
    report: DBReport = get_by_id(session, report_id)
    pdp.ensure_manage_assignee(report_id)
    assignee: DBAccount = accounts_db.get_by_id(session, assignee_id)
    ReportPolicyDecisionPoint(session, assignee).ensure_become_assignee(report_id)
    # Set the assignee
    report.moderator_id = assignee_id
    # Update status if applicable
    if report.status == "fresh":
        report.status = "assigned"
    session.add(report)
    session.commit()
    session.refresh(report)
    return report

def remove_assignee(
    session: DBSession, # type: ignore
    pdp: ReportPolicyDecisionPoint,
    report_id: str,
) -> DBReport:
    """Removes assignee and returns a report."""
    report: DBReport = get_by_id(session, report_id)
    pdp.ensure_manage_assignee(report_id)
    report.moderator_id = None
    report.status = "fresh"
    session.add(report)
    session.commit()
    session.refresh(report)
    return report
