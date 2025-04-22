"""Request and response models for reports"""

from pydantic import BaseModel, model_validator
from datetime import datetime
from typing import Any

from backend.models.shared import Metadata
from backend.database.schema import DBReport

class Report(BaseModel):
    """Response model for a report object"""
    id: str
    account_id: str
    entity_id: str
    entity_type: str
    report_type: str
    report_text: str
    status: str
    moderator_id: str | None = None
    created_at: datetime
    resolved_at: datetime | None = None

class ReportCollection(BaseModel):
    """Response model for a list of reports"""
    metadata: Metadata
    reports: list[Report]

    @model_validator(mode='before')
    def convert_list(cls, obj: Any) -> Any:
        """If this is a list[DBReport], convert to a report collection straightaway."""
        if isinstance(obj, list):
            if all([ isinstance(e, DBReport) for e in obj ]):
                return ReportCollection(
                    metadata=Metadata(count=len(obj)),
                    reports=[ Report.model_validate(report.__dict__) for report in obj ]
                ).model_dump()
        return obj

class ReportCreate(BaseModel):
    """Request model for creating a report"""
    entity_id: str
    entity_type: str
    report_type: str
    report_text: str

class ReportUpdate(BaseModel):
    """Request model for updating a report as the submitting account"""
    report_text: str | None

class StaffReportUpdate(BaseModel):
    """Request model for updating a report as the staff member"""
    status: str | None