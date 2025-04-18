"""Router for boards routes.

Args:
    router (APIRouter): Router for /boards routes
"""

from fastapi import APIRouter, Response
from uuid import UUID

from backend.database.schema import *
from backend.database import boards as boards_db
from backend.dependencies import DBSession, CurrentAccount, OptionalAccount
from backend.utils.permissions import BoardPDP
from backend.models.boards import Board, BoardCollection, BoardCreate, BoardUpdate, BoardTransfer, EditorInvitation, convert_board_list
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
    pdp: BoardPDP
) -> BoardCollection:
    """Returns a BoardCollection of boards that the currently logged-in account can edit"""
    boards = convert_board_list( boards_db.get_editable(session, pdp) )
    return BoardCollection(
        metadata=Metadata(count=len(boards)),
        boards=boards
    )

@router.post("/", status_code=201, response_model=Board)
def create_board(
    session: DBSession, # type: ignore
    pdp: BoardPDP,
    config: BoardCreate
) -> DBBoard:
    """Creates a board owned by the authenticated account"""
    return boards_db.create(session, pdp, config)

# Other routes should not be accessed by the user directly so should only depend on ID

@router.get("/{board_id:uuid}/", status_code=200, response_model=Board)
def get_board(
    session: DBSession, # type: ignore
    board_id: UUID,
    account: OptionalAccount = None
) -> DBBoard:
    """Returns the board with this ID if the account can access it"""
    return boards_db.get_for_viewer(session, str(board_id), account)

@router.get("/{username}-{identifier}/", status_code=200, response_model=Board)
def get_board_by_name_and_id(
    session: DBSession, # type: ignore
    username: str,
    identifier: str,
    account: OptionalAccount = None,
) -> DBBoard:
    """Returns the board with this ID and name if it exists and the account can view it."""
    return boards_db.get_by_name_identifier(session, username, identifier, account)

@router.put("/{board_id}/", status_code=200, response_model=Board)
def update_board(
    session: DBSession, # type: ignore
    board_id: UUID,
    pdp: BoardPDP,
    config: BoardUpdate,
) -> DBBoard:
    """Updates a board with this ID, if the authenticated account is the owner"""
    return boards_db.update(session, pdp, str(board_id), config)

@router.delete("/{board_id}/", status_code=204)
def delete_board(
    session: DBSession, # type: ignore
    pdp: BoardPDP,
    board_id: UUID,
) -> None:
    """Deletes the board with this ID if the account is the owner"""
    boards_db.delete(session, pdp, str(board_id))

@router.get("/{board_id}/editors", status_code=200, response_model=AccountCollection)
def get_editors(
    session: DBSession, # type: ignore
    pdp: BoardPDP,
    board_id: UUID,
) -> AccountCollection:
    """Gets all accounts that can edit the board with this ID, excluding the owner."""
    editors = convert_account_list( boards_db.get_editors(session, pdp, str(board_id)) )
    return AccountCollection(
        metadata=Metadata(count=len(editors)),
        accounts=editors
    )

@router.post("/{board_id}/editors", status_code=204, response_model=None)
def add_editor(
    session: DBSession, # type: ignore
    pdp: BoardPDP,
    board_id: UUID,
    invitation: EditorInvitation,
) -> None:
    """Invites an account to edit this board"""
    boards_db.invite_editor(session, pdp, str(board_id), invitation)

@router.delete("/{board_id}/editors/{editor_id}", status_code=200, response_model=AccountCollection)
def remove_editor(
    session: DBSession, # type: ignore
    pdp: BoardPDP,
    board_id: UUID,
    editor_id: UUID,
) -> AccountCollection:
    """Disallows the account with this ID to edit the board with this ID, and returns the updated list of editors."""
    editors = convert_account_list( boards_db.remove_editor(session, pdp, str(board_id), str(editor_id)) )
    return AccountCollection(
        metadata=Metadata(count=len(editors)),
        accounts=editors
    )

@router.post("/{board_id}/transfer", status_code=200, response_model=Board)
def transfer_board(
    session: DBSession, # type: ignore
    pdp: BoardPDP,
    board_id: UUID,
    transfer: BoardTransfer,
) -> DBBoard:
    """Transfers the board to another editor account, rendering this account as an editor. Returns the updated board."""
    return boards_db.transfer_board(session, pdp, str(board_id), transfer)

@router.post("/accept-invite/{invitation:uuid}", status_code=200, response_model=Board)
def transfer_board(
    session: DBSession, # type: ignore
    invitation: UUID,
) -> DBBoard:
    """Transfers the board to another editor account, rendering this account as an editor. Returns the updated board."""
    return boards_db.accept_editor_invitation(session, str(invitation))