"""Router for boards routes.

Args:
    router (APIRouter): Router for /boards routes
"""

from fastapi import APIRouter, Request
from uuid import UUID

from backend.database.schema import *
from backend.database import boards as boards_db
from backend.dependencies import DBSession, OptionalAccount
from backend.utils.permissions import BoardPDP
from backend.utils.rate_limiter import limit
from backend.models.boards import Board, BoardCreate, BoardUpdate, BoardTransfer, EditorInvitation
from backend.models.accounts import Account
from backend.models.shared import CollectionFactory

router = APIRouter(prefix="/boards", tags=["Board"])

@router.get("/", status_code=200, response_model=CollectionFactory(Board, DBBoard))
@limit("board")
def get_boards(
    request: Request,
    session: DBSession, # type: ignore
    account: OptionalAccount = None
) -> list[DBBoard]:
    """Returns a collection of all visible boards, including both public ones and editable ones"""
    return boards_db.get_visible(session, account)

@router.get("/editable", status_code=200, response_model=CollectionFactory(Board, DBBoard))
@limit("board")
def get_editable_boards(
    request: Request,
    session: DBSession, # type: ignore
    pdp: BoardPDP
) -> list[DBBoard]:
    """Returns a collection of boards that the currently logged-in account can edit"""
    return boards_db.get_editable(session, pdp)

@router.post("/", status_code=201, response_model=Board)
@limit("board")
def create_board(
    request: Request,
    session: DBSession, # type: ignore
    pdp: BoardPDP,
    config: BoardCreate
) -> DBBoard:
    """Creates a board owned by the authenticated account"""
    return boards_db.create(session, pdp, config)

# Other routes should not be accessed by the user directly so should only depend on ID

@router.get("/{board_id:uuid}/", status_code=200, response_model=Board)
@limit("board")
def get_board(
    request: Request,
    session: DBSession, # type: ignore
    board_id: UUID,
    account: OptionalAccount = None
) -> DBBoard:
    """Returns the board with this ID if the account can access it"""
    return boards_db.get_for_viewer(session, str(board_id), account)

@router.get("/{username}-{identifier}/", status_code=200, response_model=Board)
@limit("board")
def get_board_by_name_and_id(
    request: Request,
    session: DBSession, # type: ignore
    username: str,
    identifier: str,
    account: OptionalAccount = None,
) -> DBBoard:
    """Returns the board with this ID and name if it exists and the account can view it."""
    return boards_db.get_by_name_identifier(session, username, identifier, account)

@router.put("/{board_id}/", status_code=200, response_model=Board)
@limit("board")
def update_board(
    request: Request,
    session: DBSession, # type: ignore
    board_id: UUID,
    pdp: BoardPDP,
    config: BoardUpdate,
) -> DBBoard:
    """Updates a board with this ID, if the authenticated account is the owner"""
    return boards_db.update(session, pdp, str(board_id), config)

@router.delete("/{board_id}/", status_code=204)
@limit("board", no_content=True)
def delete_board(
    request: Request,
    session: DBSession, # type: ignore
    pdp: BoardPDP,
    board_id: UUID,
) -> None:
    """Deletes the board with this ID if the account is the owner"""
    boards_db.delete(session, pdp, str(board_id))

@router.get("/{board_id}/editors", status_code=200, response_model=CollectionFactory(Account, DBAccount))
@limit("board")
def get_editors(
    request: Request,
    session: DBSession, # type: ignore
    pdp: BoardPDP,
    board_id: UUID,
) -> list[DBAccount]:
    """Gets all accounts that can edit the board with this ID, excluding the owner."""
    return boards_db.get_editors(session, pdp, str(board_id))

@router.post("/{board_id}/editors", status_code=204, response_model=None)
@limit("board", no_content=True)
def add_editor(
    request: Request,
    session: DBSession, # type: ignore
    pdp: BoardPDP,
    board_id: UUID,
    invitation: EditorInvitation,
) -> None:
    """Invites an account to edit this board"""
    boards_db.invite_editor(session, pdp, str(board_id), invitation)

@router.delete("/{board_id}/editors/{editor_id}", status_code=200, response_model=CollectionFactory(Account, DBAccount))
@limit("board")
def remove_editor(
    request: Request,
    session: DBSession, # type: ignore
    pdp: BoardPDP,
    board_id: UUID,
    editor_id: UUID,
) -> list[DBAccount]:
    """Disallows the account with this ID to edit the board with this ID, and returns the updated list of editors."""
    return boards_db.remove_editor(session, pdp, str(board_id), str(editor_id))

@router.post("/{board_id}/transfer", status_code=200, response_model=Board)
@limit("board")
def transfer_board(
    request: Request,
    session: DBSession, # type: ignore
    pdp: BoardPDP,
    board_id: UUID,
    transfer: BoardTransfer,
) -> DBBoard:
    """Transfers the board to another editor account, rendering this account as an editor. Returns the updated board."""
    return boards_db.transfer_board(session, pdp, str(board_id), transfer)

@router.post("/accept-invite/{invitation:uuid}", status_code=200, response_model=Board)
@limit("from_email")
def transfer_board(
    request: Request,
    session: DBSession, # type: ignore
    invitation: UUID,
) -> DBBoard:
    """Transfers the board to another editor account, rendering this account as an editor. Returns the updated board."""
    return boards_db.accept_editor_invitation(session, str(invitation))