"""Request and response models for reports"""

from pydantic import BaseModel
from datetime import datetime

from backend.models.shared import Metadata

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
    resolved_at: datetime

class ReportCollection(BaseModel):
    """Response model for a list of reports"""
    metadata: Metadata
    reports: []

class ReportCreate(BaseModel):
    """Request model for creating a report"""
    entity_id: str
    entity_type: str
    report_type: str
    report_text: str

class ReportUpdate(BaseModel):
    """Request model for updating a report as the submitting account"""
    report_text: str

class StaffReportUpdate(BaseModel):
    """Request model for updating a report as the staff member"""
    status: str