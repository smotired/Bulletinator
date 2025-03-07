"""Request and response models for board functionality"""

from pydantic import BaseModel
import shared

class Board(BaseModel):
    """Response model for a board"""
    id: int
    name: str
    icon: str
    owner_id: int
    public: bool
    
class BoardCollection(BaseModel):
    """Response model for a collection of boards"""
    metadata: shared.Metadata
    boards: list[Board]
    
class BoardCreate(BaseModel):
    """Request model for creating a board"""
    name: str
    icon: str = "default"
    public: bool = False
    
class BoardUpdate(BaseModel):
    """Request model for updating a board"""
    name: str | None = None
    icon: str | None = None
    public: bool | None = None