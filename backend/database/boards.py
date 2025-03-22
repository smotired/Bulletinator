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
    if not board.public and user != board.owner and user not in board.editors:
        raise EntityNotFound("board", "id", board_id)
    return board

def get_editable(session, DBSession, user: DBUser) -> list[DBBoard]:
    """Returns a list of all boards editable by this user"""
    stmt = select(DBBoard).where(DBBoard.owner == user)
    owned = list(session.execute(stmt).all())
    stmt = select(DBBoard).where(user in DBBoard.editors)
    editable = list(session.execute(stmt).all())
    return owned + editable # make sure owners cannot add themselves as editors

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