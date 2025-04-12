"""Router for boards routes.

Args:
    router (APIRouter): Router for /boards routes
"""

from fastapi import APIRouter, Depends

from backend.database.schema import *
from backend.database import boards as boards_db
from backend.dependencies import DBSession, CurrentAccount, OptionalAccount
from backend.models.boards import Board, BoardCollection, BoardCreate, BoardUpdate, convert_board_list
from backend.models.accounts import AccountCollection, convert_account_list
from backend.models.shared import Metadata

router = APIRouter(prefix="/boards", tags=["Board"])

@router.get("/", status_code=200)
def get_boards(
    session: DBSession, # type: ignore
    account: OptionalAccount = None
) -> BoardCollection:
    """Returns a BoardCollection of all visible boards, including both public ones and editable ones"""
    boards = convert_board_list( boards_db.get_visible(session, account) )
    return BoardCollection(
        metadata=Metadata(count=len(boards)),
        boards=boards
    )

@router.get("/editable", status_code=200)
def get_editable_boards(
    session: DBSession, # type: ignore
    account: CurrentAccount
) -> BoardCollection:
    """Returns a BoardCollection of boards that the currently logged-in account can edit"""
    boards = convert_board_list( boards_db.get_editable(session, account) )
    return BoardCollection(
        metadata=Metadata(count=len(boards)),
        boards=boards
    )

@router.post("/", status_code=201, response_model=Board)
def create_board(
    session: DBSession, # type: ignore
    account: CurrentAccount,
    config: BoardCreate
) -> DBBoard:
    """Creates a board owned by the authenticated account"""
    return boards_db.create(session, account, config)

@router.get("/{board_id}/", status_code=200, response_model=Board)
def get_board(
    session: DBSession, # type: ignore
    board_id: int,
    account: OptionalAccount = None
) -> DBBoard:
    """Returns the board with this ID if the account can access it"""
    return boards_db.get_for_viewer(session, board_id, account)

@router.put("/{board_id}/", status_code=200, response_model=Board)
def update_board(
    session: DBSession, # type: ignore
    board_id: int,
    account: CurrentAccount,
    config: BoardUpdate
) -> DBBoard:
    """Updates a board with this ID, if the authenticated account is the owner"""
    return boards_db.update(session, account, board_id, config)

@router.delete("/{board_id}/", status_code=204)
def delete_board(
    session: DBSession, # type: ignore
    board_id: int,
    account: CurrentAccount
) -> None:
    """Deletes the board with this ID if the account is the owner"""
    boards_db.delete(session, account, board_id)

@router.get("/{board_id}/editors", status_code=200, response_model=AccountCollection)
def get_editors(
    session: DBSession, # type: ignore
    board_id: int,
    account: CurrentAccount
) -> AccountCollection:
    """Gets all accounts that can edit the board with this ID, excluding the owner."""
    editors = convert_account_list( boards_db.get_editors(session, account, board_id) )
    return AccountCollection(
        metadata=Metadata(count=len(editors)),
        accounts=editors
    )

@router.put("/{board_id}/editors/{editor_id}", status_code=201, response_model=AccountCollection)
def add_editor(
    session: DBSession, # type: ignore
    board_id: int,
    editor_id: int,
    account: CurrentAccount
) -> AccountCollection:
    """Allows the account with this ID to edit the board with this ID, and returns the updated list of editors."""
    editors = convert_account_list( boards_db.add_editor(session, account, board_id, editor_id) )
    return AccountCollection(
        metadata=Metadata(count=len(editors)),
        accounts=editors
    )

@router.delete("/{board_id}/editors/{editor_id}", status_code=200, response_model=AccountCollection)
def remove_editor(
    session: DBSession, # type: ignore
    board_id: int,
    editor_id: int,
    account: CurrentAccount
) -> AccountCollection:
    """Disallows the account with this ID to edit the board with this ID, and returns the updated list of editors."""
    editors = convert_account_list( boards_db.remove_editor(session, account, board_id, editor_id) )
    return AccountCollection(
        metadata=Metadata(count=len(editors)),
        accounts=editors
    )