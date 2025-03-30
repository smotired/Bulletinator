from sqlalchemy import select

from backend.dependencies import DBSession
from backend.database import users as users_db
from backend.database.schema import DBBoard, DBUser
from backend.exceptions import *

from backend.models.boards import BoardCreate, BoardUpdate

def can_edit(session: DBSession, board: DBBoard, user: DBUser) -> bool:
    """Returns true if this user can edit the items on this board (i.e. they're the owner or they're an editor)"""
    return board.owner == user or user in board.editors

def can_see(session: DBSession, board: DBBoard, user: DBUser) -> bool:
    """Returns true if this user can see this board (i.e. it's public, they're the owner, or they're an editor)"""
    return board.public or can_edit(session, board, user)

def get_by_id(session: DBSession, board_id: int) -> DBBoard:
    """Returns the board with this ID"""
    board = session.get(DBBoard, board_id)
    if board is None:
        raise EntityNotFound("board", "id", board_id)
    return board

def get_board(session: DBSession, user: DBUser | None, board_id: int) -> DBBoard:
    """Returns a board if it's public or the current user can edit it. Raise a 404 if private."""
    board = get_by_id(session, board_id)
    if not board.public and (user is None or ( user.id != board.owner_id and user.id not in [editor.id for editor in board.editors ])):
        raise EntityNotFound("board", "id", board_id)
    return board

def get_all(session: DBSession) -> list[DBBoard]:
    """Returns a list of all boards ordered by name"""
    stmt = select(DBBoard).order_by(DBBoard.name)
    return list(session.execute(stmt).scalars().all())

def get_visible(session: DBSession, user: DBUser | None) -> list[DBBoard]:
    """Returns a list of all boards, ordered by name, that the user can see.
    
    If not logged in, this is all public boards. If logged in, also includes private boards they can access."""
    stmt = select(DBBoard).where(DBBoard.public).order_by(DBBoard.name)
    public = list(session.execute(stmt).scalars().all())
    editable = [] if user is None else get_editable(session, user)

    # join them into a list making sure not to add duplicates
    union = public + [ board for board in editable if board not in public ]
    return sorted(union, key=lambda b: b.name)

def get_editable(session: DBSession, user: DBUser) -> list[DBBoard]:
    """Returns a list of all boards editable by this user, ordered by name"""
    stmt = select(DBBoard).where(DBBoard.owner_id == user.id).order_by(DBBoard.name)
    owned = list(session.execute(stmt).scalars().all())
    stmt = select(DBBoard).join(DBBoard.editors).where(DBUser.id == user.id).order_by(DBBoard.name)
    editable = list(session.execute(stmt).scalars().all())
    return sorted(owned + editable, key=lambda b: b.name) # later, make sure owners cannot add themselves as editors

def create(session: DBSession, user: DBBoard, config: BoardCreate) -> DBBoard:
    """Create a board owned by this user"""
    new_board = DBBoard(
        name=config.name,
        icon=config.icon,
        public=config.public,
        owner=user
    )
    session.add(new_board)
    session.commit()
    session.refresh(new_board)
    return new_board

def update(session: DBSession, user: DBUser, board_id: int, config: BoardUpdate) -> DBBoard:
    """Update a board owned by this user"""
    board = get_by_id(session, board_id)
    # Make sure the board is actually owned by this user (editors shouldn't be able to change name, icon, or publicity)
    if user != board.owner:
        if not can_see(session, board, user):
            raise EntityNotFound("board", "id", board_id) # do not even say the board exists
        raise AccessDenied()
    # Update it
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

def delete(session: DBSession, user: DBUser, board_id: int) -> None:
    """Delete a board owned by this user"""
    board = get_by_id(session, board_id)
    if user != board.owner:
        if not can_see(session, board, user):
            raise EntityNotFound("board", "id", board_id) # do not even say the board exists
        raise AccessDenied()
    session.delete(board)
    session.commit()

def get_editors(session: DBSession, user: DBUser, board_id: int) -> list[DBUser]:
    """Get a list of editors on this board. Editors can be seen by other editors."""
    board = get_by_id(session, board_id)
    if not can_edit(session, board, user):
        if not can_see(session, board, user):
            raise EntityNotFound("board", "id", board_id) # do not even say the board exists
        raise AccessDenied()
    return board.editors

def add_editor(session: DBSession, user: DBUser, board_id: int, editor_id: int) -> list[DBUser]:
    """Allow another user to edit this board. Returns the updated list of editors."""
    board = get_by_id(session, board_id)
    if user != board.owner:
        if not can_see(session, board, user):
            raise EntityNotFound("board", "id", board_id) # do not even say the board exists
        raise AccessDenied()
    editor = users_db.get_by_id(session, editor_id)
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
    return board.editors

def remove_editor(session: DBSession, user: DBUser, board_id: int, editor_id: int) -> list[DBUser]:
    """Remove an editor from a board and return the updated list of editors"""
    board = get_by_id(session, board_id)
    if user != board.owner:
        if not can_see(session, board, user):
            raise EntityNotFound("board", "id", board_id) # do not even say the board exists
        raise AccessDenied()
    editor = users_db.get_by_id(session, editor_id)
    board.editors = [ e for e in board.editors if e != editor ]
    session.add(board)
    session.commit()
    session.refresh(board)
    return board.editors