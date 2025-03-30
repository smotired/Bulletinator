from sqlalchemy import select

from backend.dependencies import DBSession
from backend.database import users as users_db
from backend.database.schema import DBBoard, DBUser
from backend.exceptions import *

from backend.models.boards import BoardCreate, BoardUpdate

def can_edit(board: DBBoard, user: DBUser | None) -> bool:
    """Returns true if this user can edit the items on this board (i.e. they're the owner or they're an editor)"""
    if not user:
        return False
    return board.owner == user or user in board.editors

def can_see(board: DBBoard, user: DBUser | None) -> bool:
    """Returns true if this user can see this board (i.e. it's public, they're the owner, or they're an editor)"""
    return board.public or (user is not None and can_edit(board, user))

def get_by_id(session: DBSession, board_id: int) -> DBBoard:
    """Returns the board with this ID"""
    board = session.get(DBBoard, board_id)
    if board is None:
        raise EntityNotFound("board", "id", board_id)
    return board

def get_for_owner(session: DBSession, board_id: DBBoard, user: DBUser | None) -> DBBoard:
    """Returns the board with this ID if the user is the owner, or returns exceptions based on if the user can see it"""
    board: DBBoard = get_by_id(session, board_id)
    if can_see(board, user):
        if user is not None and board.owner == user:
            return board
        else:
            raise AccessDenied()
    else:
        raise EntityNotFound("board", "id", board_id)

def get_for_editor(session: DBSession, board_id: DBBoard, user: DBUser | None) -> DBBoard:
    """Returns the board with this ID if the user is the owner, or returns exceptions based on if the user can see it"""
    board: DBBoard = get_by_id(session, board_id)
    if can_see(board, user):
        if can_edit(board, user):
            return board
        else:
            raise AccessDenied()
    else:
        raise EntityNotFound("board", "id", board_id)

def get_for_viewer(session: DBSession, board_id: DBBoard, user: DBUser | None) -> DBBoard:
    """Returns the board with this ID if the user can see this board, or returns a 404."""
    board: DBBoard = get_by_id(session, board_id)
    if can_see(board, user):
        return board
    else:
        raise EntityNotFound("board", "id", board_id)

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
    board = get_for_owner(session, board_id, user)
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
    board = get_for_owner(session, board_id, user)
    session.delete(board)
    session.commit()

def get_editors(session: DBSession, user: DBUser, board_id: int) -> list[DBUser]:
    """Get a list of editors on this board. Editors can be seen by other editors."""
    board = get_for_editor(session, board_id, user)
    return board.editors

def add_editor(session: DBSession, user: DBUser, board_id: int, editor_id: int) -> list[DBUser]:
    """Allow another user to edit this board. Returns the updated list of editors."""
    board = get_for_owner(session, board_id, user)
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
    board = get_for_owner(session, board_id, user)
    editor = users_db.get_by_id(session, editor_id)
    board.editors = [ e for e in board.editors if e != editor ]
    session.add(board)
    session.commit()
    session.refresh(board)
    return board.editors