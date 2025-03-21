from sqlalchemy import select

from backend.dependencies import DBSession
from backend.database.schema import DBBoard, DBUser
from backend.exceptions import *

from backend.models.boards import BoardCreate, BoardUpdate

def get_editable(session, user) -> list[DBBoard]:
    """Returns a list of all boards editable by this user"""
    stmt = select(DBBoard).where(DBBoard.owner == user)
    owned = list(session.execute(stmt).all())
    stmt = select(DBBoard).where(user in DBBoard.editors)
    editable = list(session.execute(stmt).all())
    return owned + editable # make sure owners cannot add themselves as editors