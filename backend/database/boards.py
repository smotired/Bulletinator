from sqlalchemy import select
import re

from backend.dependencies import DBSession, name_to_identifier
from backend.database import accounts as accounts_db
from backend.database.schema import DBBoard, DBAccount
from backend.exceptions import *

from backend.models.boards import BoardCreate, BoardUpdate

def can_edit(board: DBBoard, account: DBAccount | None) -> bool:
    """Returns true if this account can edit the items on this board (i.e. they're the owner or they're an editor)"""
    if not account:
        return False
    return board.owner == account or account in board.editors

def can_see(board: DBBoard, account: DBAccount | None) -> bool:
    """Returns true if this account can see this board (i.e. it's public, they're the owner, or they're an editor)"""
    return board.public or (account is not None and can_edit(board, account))

def get_by_id(session: DBSession, board_id: str) -> DBBoard:
    """Returns the board with this ID"""
    board = session.get(DBBoard, board_id)
    if board is None:
        raise EntityNotFound("board", "id", board_id)
    return board

def get_for_owner(session: DBSession, board_id: str, account: DBAccount | None) -> DBBoard:
    """Returns the board with this ID if the account is the owner, or returns exceptions based on if the account can see it"""
    board: DBBoard = get_by_id(session, board_id)
    if can_see(board, account):
        if account is not None and board.owner == account:
            return board
        else:
            raise AccessDenied()
    else:
        raise EntityNotFound("board", "id", board_id)

def get_for_editor(session: DBSession, board_id: str, account: DBAccount | None) -> DBBoard:
    """Returns the board with this ID if the account is the owner, or returns exceptions based on if the account can see it"""
    board: DBBoard = get_by_id(session, board_id)
    if can_see(board, account):
        if can_edit(board, account):
            return board
        else:
            raise AccessDenied()
    else:
        raise EntityNotFound("board", "id", board_id)

def get_for_viewer(session: DBSession, board_id: str, account: DBAccount | None) -> DBBoard:
    """Returns the board with this ID if the account can see this board, or returns a 404."""
    board: DBBoard = get_by_id(session, board_id)
    if can_see(board, account):
        return board
    else:
        raise EntityNotFound("board", "id", board_id)

def get_all(session: DBSession) -> list[DBBoard]:
    """Returns a list of all boards ordered by name"""
    stmt = select(DBBoard).order_by(DBBoard.name)
    return list(session.execute(stmt).scalars().all())

def get_visible(session: DBSession, account: DBAccount | None) -> list[DBBoard]:
    """Returns a list of all boards, ordered by name, that the account can see.
    
    If not logged in, this is all public boards. If logged in, also includes private boards they can access."""
    stmt = select(DBBoard).where(DBBoard.public).order_by(DBBoard.name)
    public = list(session.execute(stmt).scalars().all())
    editable = [] if account is None else get_editable(session, account)

    # join them into a list making sure not to add duplicates
    union = public + [ board for board in editable if board not in public ]
    return sorted(union, key=lambda b: b.name)

def get_editable(session: DBSession, account: DBAccount) -> list[DBBoard]:
    """Returns a list of all boards editable by this account, ordered by name"""
    stmt = select(DBBoard).where(DBBoard.owner_id == account.id).order_by(DBBoard.name)
    owned = list(session.execute(stmt).scalars().all())
    stmt = select(DBBoard).join(DBBoard.editors).where(DBAccount.id == account.id).order_by(DBBoard.name)
    editable = list(session.execute(stmt).scalars().all())
    return sorted(owned + editable, key=lambda b: b.name)

def get_by_name_identifier(session: DBSession, username: str, identifier: str, account: DBAccount) -> DBBoard:
    """Attempts to fetch a board by an ID and identifier"""
    owner: DBAccount = accounts_db.get_by_username(session, username)
    if owner is None:
        raise EntityNotFound('account', 'username', username)
    statement = select(DBBoard).where(DBBoard.owner_id == owner.id).where(DBBoard.identifier == identifier)
    boards: list[DBBoard] = list( session.execute(statement).scalars().all() )
    if len(boards) == 0 or not can_see(boards[0], account):
        raise EntityNotFound('board', 'identifier', identifier)
    return boards[0]

def create(session: DBSession, account: DBBoard, config: BoardCreate) -> DBBoard:
    """Create a board owned by this account"""
    new_board = DBBoard(
        identifier = config.identifier or name_to_identifier(config.name),
        name=config.name,
        icon=config.icon,
        public=config.public,
        owner=account
    )
    if re.fullmatch(r"[A-Za-z0-9_]+", new_board.identifier) is None:
        raise InvalidField(new_board.identifier, 'identifier')
    # Make sure identifier is unique for this user
    statement = select(DBBoard).where(DBBoard.owner_id == account.id)
    account_boards = list( session.execute(statement).scalars().all() )
    if any([ board.identifier == new_board.identifier for board in account_boards ]):
        raise DuplicateEntity('board', 'identifier', new_board.identifier)
    # Add it
    session.add(new_board)
    session.commit()
    session.refresh(new_board)
    return new_board

def update(session: DBSession, account: DBAccount, board_id: str, config: BoardUpdate) -> DBBoard:
    """Update a board owned by this account"""
    board = get_for_owner(session, board_id, account)
    # Update it
    if config.identifier is not None and config.identifier != board.identifier:
        if re.fullmatch(r"[A-Za-z0-9_]+", config.identifier) is None:
            raise InvalidField(config.identifier, 'identifier')
        # Make sure identifier is unique for this user
        statement = select(DBBoard).where(DBBoard.owner_id == account.id)
        account_boards = list( session.execute(statement).scalars().all() )
        if any([ board.identifier == config.identifier for board in account_boards ]):
            raise DuplicateEntity('board', 'identifier', config.identifier)
        board.identifier = config.identifier
    if config.name is not None:
        board.name = config.name
    if config.icon is not None:
        board.icon = config.icon
    if config.public is not None:
        board.public = config.public
    session.add(board)
    session.commit()
    session.refresh(board)
    return board

def delete(session: DBSession, account: DBAccount, board_id: str) -> None:
    """Delete a board owned by this account"""
    board = get_for_owner(session, board_id, account)
    session.delete(board)
    session.commit()

def get_editors(session: DBSession, account: DBAccount, board_id: str) -> list[DBAccount]:
    """Get a list of editors on this board. Editors can be seen by other editors."""
    board = get_for_editor(session, board_id, account)
    return sorted(board.editors, key=lambda e: e.id)

def add_editor(session: DBSession, account: DBAccount, board_id: str, editor_id: str) -> list[DBAccount]:
    """Allow another account to edit this board. Returns the updated list of editors."""
    board = get_for_owner(session, board_id, account)
    editor = accounts_db.get_by_id(session, editor_id)
    # Make sure we aren't adding the owner
    if editor == board.owner:
        raise AddBoardOwnerAsEditor()
    # Add it, unless it's already in there
    if editor not in board.editors:
        board.editors.append(editor)
    # Update and return editors
    session.add(board)
    session.commit()
    session.refresh(board)
    return sorted(board.editors, key=lambda e: e.id)

def remove_editor(session: DBSession, account: DBAccount, board_id: str, editor_id: str) -> list[DBAccount]:
    """Remove an editor from a board and return the updated list of editors"""
    board = get_for_owner(session, board_id, account)
    editor = accounts_db.get_by_id(session, editor_id)
    board.editors = [ e for e in board.editors if e != editor ]
    session.add(board)
    session.commit()
    session.refresh(board)
    return sorted(board.editors, key=lambda e: e.id)