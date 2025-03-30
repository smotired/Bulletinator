"""Router for boards routes.

Args:
    router (APIRouter): Router for /boards routes
"""

from fastapi import APIRouter, Depends

from backend.database.schema import *
from backend.database import boards as boards_db
from backend.dependencies import DBSession, CurrentUser, OptionalUser
from backend.models.boards import Board, BoardCollection, BoardCreate, BoardUpdate, convert_board_list
from backend.models.users import UserCollection, convert_user_list
from backend.models.shared import Metadata

router = APIRouter(prefix="/boards", tags=["Board"])

@router.get("/", status_code=200)
def get_boards(session: DBSession, user: OptionalUser = None) -> BoardCollection:
    """Returns a BoardCollection of all visible boards, including both public ones and editable ones"""
    boards = convert_board_list( boards_db.get_visible(session, user) )
    return BoardCollection(
        metadata=Metadata(count=len(boards)),
        boards=boards
    )

@router.get("/editable", status_code=200)
def get_editable_boards(session: DBSession, user: CurrentUser) -> BoardCollection:
    """Returns a BoardCollection of boards that the currently logged-in user can edit"""
    boards = convert_board_list( boards_db.get_editable(session, user) )
    return BoardCollection(
        metadata=Metadata(count=len(boards)),
        boards=boards
    )

@router.post("/", status_code=201, response_model=Board)
def create_board(session: DBSession, user: CurrentUser, config: BoardCreate) -> DBBoard:
    """Creates a board owned by the authenticated user"""
    return boards_db.create(session, user, config)

@router.get("/{board_id}/", status_code=200, response_model=Board)
def get_board(session: DBSession, board_id: int, user: OptionalUser = None) -> DBBoard:
    """Returns the board with this ID if the user can access it"""
    return boards_db.get_board(session, user, board_id)

@router.put("/{board_id}/", status_code=200, response_model=Board)
def update_board(session: DBSession, board_id: int, user: CurrentUser, config: BoardUpdate) -> DBBoard:
    """Updates a board with this ID, if the authenticated user is the owner"""
    return boards_db.update(session, user, board_id, config)

@router.delete("/{board_id}/", status_code=204)
def delete_board(session: DBSession, board_id: int, user: CurrentUser) -> None:
    """Deletes the board with this ID if the user is the owner"""
    boards_db.delete(session, user, board_id)

@router.get("/{board_id}/editors", status_code=200, response_model=UserCollection)
def get_editors(session: DBSession, board_id: int, user: CurrentUser) -> UserCollection:
    """Gets all users that can edit the board with this ID, excluding the owner."""
    editors = convert_user_list( boards_db.get_editors(session, user, board_id) )
    return UserCollection(
        metadata=Metadata(count=len(editors)),
        users=editors
    )

@router.put("/{board_id}/editors/{editor_id}", status_code=201, response_model=UserCollection)
def add_editor(session: DBSession, board_id: int, editor_id: int, user: CurrentUser) -> UserCollection:
    """Allows the user with this ID to edit the board with this ID, and returns the updated list of editors."""
    editors = convert_user_list( boards_db.add_editor(session, user, board_id, editor_id) )
    return UserCollection(
        metadata=Metadata(count=len(editors)),
        users=editors
    )

@router.delete("/{board_id}/editors/{editor_id}", status_code=200, response_model=UserCollection)
def remove_editor(session: DBSession, board_id: int, editor_id: int, user: CurrentUser) -> UserCollection:
    """Disallows the user with this ID to edit the board with this ID, and returns the updated list of editors."""
    editors = convert_user_list( boards_db.remove_editor(session, user, board_id, editor_id) )
    return UserCollection(
        metadata=Metadata(count=len(editors)),
        users=editors
    )