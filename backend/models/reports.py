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