from sqlalchemy import select

from backend.dependencies import DBSession
from backend.database.schema import DBBoard, DBUser
from backend.exceptions import *

from backend.models.boards import BoardCreate, BoardUpdate

def get_by_id(session: DBSession, board_id: int) -> DBBoard:
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
        raise AccessDenied()
    session.delete(board)
    session.commit()