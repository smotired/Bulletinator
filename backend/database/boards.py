from sqlalchemy import select
import re

from backend.utils.email_handler import send_editor_invitation_email
from backend.dependencies import DBSession, name_to_identifier
from backend.utils.permissions import BoardPolicyDecisionPoint
from backend.database import accounts as accounts_db
from backend.database.schema import DBBoard, DBAccount, DBEditorInvitation
from backend.exceptions import *

from backend.models.boards import BoardCreate, BoardUpdate, BoardTransfer, EditorInvitation

def can_edit(board: DBBoard, account: DBAccount | None) -> bool:
    
    """Returns true if this account can edit the items on this board (i.e. they're the owner or they're an editor)"""
    if not account:
        return False
    return board.owner == account or account in board.editors

def can_see(board: DBBoard, account: DBAccount | None) -> bool:
    """Returns true if this account can see this board (i.e. it's public, they're the owner, or they're an editor)"""
    return board.public or (account is not None and can_edit(board, account))

def get_by_id(session: DBSession, board_id: str) -> DBBoard: # type: ignore
    """Returns the board with this ID"""
    board = session.get(DBBoard, board_id)
    if board is None:
        raise EntityNotFound("board", "id", board_id)
    return board

def get_for_viewer(session: DBSession, board_id: str, account: DBAccount | None) -> DBBoard: # type: ignore
    """Returns the board with this ID if the account can see this board, or returns a 404."""
    board: DBBoard = get_by_id(session, board_id)
    if can_see(board, account):
        return board
    try:
        BoardPolicyDecisionPoint(session, account).ensure_read(board_id)
        return board
    except:
        pass
    raise EntityNotFound("board", "id", board_id)

def get_all(session: DBSession) -> list[DBBoard]: # type: ignore
    """Returns a list of all boards ordered by name"""
    stmt = select(DBBoard).order_by(DBBoard.name)
    return list(session.execute(stmt).scalars().all())

def get_visible(session: DBSession, account: DBAccount | None) -> list[DBBoard]: # type: ignore
    """Returns a list of all boards, ordered by name, that the account can see.
    
    If not logged in, this is all public boards. If logged in, also includes private boards they can access."""
    stmt = select(DBBoard).where(DBBoard.public).order_by(DBBoard.name)
    public = list(session.execute(stmt).scalars().all())
    editable = [] if account is None else get_editable(session, BoardPolicyDecisionPoint(session, account))

    # join them into a list making sure not to add duplicates
    union = public + [ board for board in editable if board not in public ]
    return sorted(union, key=lambda b: b.name)

def get_editable(session: DBSession, pdp: BoardPolicyDecisionPoint) -> list[DBBoard]: # type: ignore
    """Returns a list of all boards editable by this account, ordered by name"""
    pdp.ensure_query_all()
    stmt = select(DBBoard).where(DBBoard.owner_id == pdp.account.id).order_by(DBBoard.name)
    owned = list(session.execute(stmt).scalars().all())
    stmt = select(DBBoard).join(DBBoard.editors).where(DBAccount.id == pdp.account.id).order_by(DBBoard.name)
    editable = list(session.execute(stmt).scalars().all())
    return sorted(owned + editable, key=lambda b: b.name)

def get_by_name_identifier(session: DBSession, username: str, identifier: str, account: DBAccount | None) -> DBBoard: # type: ignore
    """Attempts to fetch a board by an ID and identifier"""
    owner: DBAccount = accounts_db.get_by_username(session, username)
    if owner is None:
        raise EntityNotFound('account', 'username', username)
    statement = select(DBBoard).where(DBBoard.owner_id == owner.id).where(DBBoard.identifier == identifier)
    boards: list[DBBoard] = list( session.execute(statement).scalars().all() )
    if len(boards) == 0 or not can_see(boards[0], account):
        raise EntityNotFound('board', 'identifier', identifier)
    return boards[0]

def create(session: DBSession, pdp: BoardPolicyDecisionPoint, config: BoardCreate) -> DBBoard: # type: ignore
    """Create a board owned by this account"""
    pdp.ensure_create()
    identifier = config.identifier or name_to_identifier(config.name)
    if re.fullmatch(r"[A-Za-z0-9_]+", identifier) is None:
        raise InvalidField(identifier, 'identifier')
    # Make sure identifier is unique for this user
    statement = select(DBBoard).where(DBBoard.owner_id == pdp.account.id)
    account_boards = list( session.execute(statement).scalars().all() )
    if any([ board.identifier == identifier for board in account_boards ]):
        raise DuplicateEntity('board', 'identifier', identifier)
    if config.identifier is not None and len(config.identifier) > 64:
        raise FieldTooLong('identifier')
    if len(config.name) > 64:
        raise FieldTooLong('name')
    if len(config.icon) > 64:
        raise FieldTooLong('icon')
    # Add it
    new_board = DBBoard(
        identifier = identifier,
        name=config.name,
        icon=config.icon,
        public=config.public,
        owner=pdp.account
    )
    session.add(new_board)
    session.commit()
    session.refresh(new_board)
    return new_board

def update(session: DBSession, pdp: BoardPolicyDecisionPoint, board_id: str, config: BoardUpdate) -> DBBoard: # type: ignore
    """Update a board owned by this account"""
    board = get_by_id(session, board_id)
    pdp.ensure_update(board_id)
    # Update it
    if config.identifier is not None and config.identifier != board.identifier:
        if re.fullmatch(r"[A-Za-z0-9_]+", config.identifier) is None:
            raise InvalidField(config.identifier, 'identifier')
        # Make sure identifier is unique for this user
        statement = select(DBBoard).where(DBBoard.owner_id == pdp.account.id)
        account_boards = list( session.execute(statement).scalars().all() )
        if any([ board.identifier == config.identifier for board in account_boards ]):
            raise DuplicateEntity('board', 'identifier', config.identifier)
        if len(config.identifier) > 64:
            raise FieldTooLong('identifier')
        board.identifier = config.identifier
    if config.name is not None:
        if len(config.name) > 64:
            raise FieldTooLong('name')
        board.name = config.name
    if config.icon is not None:
        if len(config.icon) > 64:
            raise FieldTooLong('icon')
        board.icon = config.icon
    if config.public is not None:
        board.public = config.public
    session.add(board)
    session.commit()
    session.refresh(board)
    return board

def delete(session: DBSession, pdp: BoardPolicyDecisionPoint, board_id: str) -> None: # type: ignore
    """Delete a board owned by this account"""
    board = get_by_id(session, board_id)
    pdp.ensure_delete(board_id)
    session.delete(board)
    session.commit()

def get_editors(session: DBSession, pdp: BoardPolicyDecisionPoint, board_id: str) -> list[DBAccount]: # type: ignore
    """Get a list of editors on this board. Editors can be seen by other editors."""
    board = get_by_id(session, board_id)
    pdp.ensure_view_editors(board_id)
    return sorted(board.editors, key=lambda e: e.id)

def invite_editor(session: DBSession, pdp: BoardPolicyDecisionPoint, board_id: str, invitation: EditorInvitation) -> bool: # type: ignore
    """Invites another user to edit this board. Sends an invitation email and returns True if they were invited, or returns False if they were already an editor."""
    board = get_by_id(session, board_id)
    pdp.ensure_manage_editors(board_id)
    editor: DBAccount | None = accounts_db.get_by_email(session, invitation.email)
    if editor is not None:
        # Make sure we aren't adding the owner
        BoardPolicyDecisionPoint(session, editor).ensure_become_editor(board_id)
        # Make sure they aren't already an editor
        if editor in board.editors:
            return False
    # Create an invitation
    invitation = DBEditorInvitation( board_id=board_id, email=invitation.email )
    session.add(invitation)
    session.commit()
    session.refresh(invitation)
    # Send the email
    send_editor_invitation_email(board, invitation, invitation.email)
    return True

def remove_editor(session: DBSession, pdp: BoardPolicyDecisionPoint, board_id: str, editor_id: str) -> list[DBAccount]: # type: ignore
    """Remove an editor from a board and return the updated list of editors"""
    board = get_by_id(session, board_id)
    pdp.ensure_remove_editor(board_id, editor_id)
    editor = accounts_db.get_by_id(session, editor_id)
    board.editors = [ e for e in board.editors if e != editor ]
    session.add(board)
    session.commit()
    session.refresh(board)
    return sorted(board.editors, key=lambda e: e.id)

def transfer_board(session: DBSession, pdp: BoardPolicyDecisionPoint, board_id: str, transfer: BoardTransfer) -> DBBoard: # type: ignore
    """Transfers a board to an editor"""
    board = get_by_id(session, board_id)
    pdp.ensure_transfer(board_id)
    other = accounts_db.get_by_id(session, transfer.account_id)
    BoardPolicyDecisionPoint(session, other).ensure_become_owner(board_id)
    board.owner_id = transfer.account_id
    board.editors.remove(other)
    board.editors.append(pdp.account)
    session.add(board)
    session.commit()
    session.refresh(board)
    return board

def accept_editor_invitation(session: DBSession, invitation_id: str) -> DBBoard: # type: ignore
    """Accepts an invitation to be an editor and returns the new board"""
    invitation: DBEditorInvitation = session.get(DBEditorInvitation, invitation_id)
    board: DBBoard = get_by_id(session, invitation.board_id) # don't use the relationship, to make sure it hasn't been deleted since
    account: DBAccount | None = accounts_db.get_by_email(session, invitation.email)
    if account is None:
        raise EntityNotFound('account', 'email', invitation.email)
    if account not in board.editors:
        board.editors.append(account)
    session.delete(invitation)
    session.add(board)
    session.commit()
    session.refresh(board)
    return board