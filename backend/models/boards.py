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
    
class BoardCollection(BaseModel):
    """Response model for a collection of boards"""
    metadata: shared.Metadata
    boards: list[Board]
    
class BoardCreate(BaseModel):
    """Request model for creating a board"""
    identifier: str | None = None # if not provided, generate one
    name: str
    icon: str = "default"
    public: bool = False
    
class BoardUpdate(BaseModel):
    """Request model for updating a board"""
    identifier: str | None = None
    name: str | None = None
    icon: str | None = None
    public: bool | None = None

def convert_board(db_board: DBBoard):
    return Board.model_validate(db_board.__dict__)

def convert_board_list(db_boards: list[DBBoard]):
    return [ convert_board(db_board) for db_board in db_boards ]