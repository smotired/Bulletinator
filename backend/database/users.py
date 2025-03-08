from backend.dependencies import Session
from backend.database.schema import DBUser
from backend.exceptions import *

def get_by_email(session: Session, email: str) -> DBUser:
    pass

def get_by_username(session: Session, username: str) -> DBUser:
    pass