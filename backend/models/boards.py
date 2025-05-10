"""Request and response models for board functionality"""

from pydantic import BaseModel
from backend.models import shared
from backend.database.schema import DBBoard

class Board(BaseModel):
    """Response model for a board"""
    id: str
    identifier: str
    name: str
    icon: str
    owner_id: str
    public: bool
    
class BoardCreate(BaseModel):
    """Request model for creating a board"""
    identifier: str | None = None # if not provided, generate one
    name: str
    icon: str = "default"
    public: bool = False
    reference_id: str | None = None # ID of the board to copy editors to
    
class BoardUpdate(BaseModel):
    """Request model for updating a board"""
    identifier: str | None = None
    name: str | None = None
    icon: str | None = None
    public: bool | None = None

class BoardTransfer(BaseModel):
    """Request model for transferring a board to another account"""
    account_id: str

class EditorInvitation(BaseModel):
    """Request model for inviting an editor account"""
    email: str