"""Functionality for permissions"""

from abc import ABC as AbstractBaseClass, abstractmethod
from fastapi import Depends
from typing import Annotated

from backend.dependencies import DBSession, CurrentAccount
from backend.database.schema import DBAccount, DBBoard
from backend.exceptions import *

class PolicyInformationPoint():
    """Used to determine relationships between accounts and other objects"""
    def __init__(self, session: DBSession, account: DBAccount): # type: ignore
        self.session = session
        self.account = account

    def is_app_staff(self) -> bool:
        return self.account.permission.role in [ 'app_administrator', 'app_moderator' ]

    def is_board_owner(self, target: DBBoard | str) -> bool:
        board: DBBoard = target if isinstance(target, DBBoard) else self.session.get(DBBoard, target)
        return board is not None and board.owner_id == self.account.id

    def is_board_editor(self, target: DBBoard | str) -> bool:
        board: DBBoard = target if isinstance(target, DBBoard) else self.session.get(DBBoard, target)
        return board is not None and self.account.id in [ editor.id for editor in board.editors ]
    
class PolicyDecisionPoint(AbstractBaseClass):
    """Uses a PIP determine permissions in relation to other objects. Throws exceptions if the permissions are not met."""
    def __init__(self, session: DBSession, account: DBAccount): # type: ignore
        self.session = session
        self.account = account
        self.pip = PolicyInformationPoint(session, account)

    @abstractmethod
    def ensure_create(self):
        """Ensure the account can create this type of object"""

    @abstractmethod
    def ensure_read_all(self):
        """Ensure the account can view this type of object."""

    @abstractmethod
    def ensure_read(self, target_id: str):
        """Ensure the account can view this specific object"""

    @abstractmethod
    def ensure_update(self, target_id: str):
        """Ensure the account can update this specific object"""

    @abstractmethod
    def ensure_delete(self, target_id: str):
        """Ensure the account can delete this specific object"""

class BoardPolicyDecisionPoint(PolicyDecisionPoint):
    """Handles permissions for boards"""
    def ensure_create(self): # Anyone can create a board
        pass

    def ensure_read_all(self): # Only staff can see all boards
        if not self.pip.is_app_staff():
            raise NoPermissions("view all boards", "account", self.account.id)
    
    def ensure_query_all(self): # Anyone can get a list of boards
        pass

    def ensure_read(self, target_id): # Can view a specific board if they are the owner, they are the editor, or it is public.
        if self.pip.is_app_staff():
            return # staff users automatically get permissions
        board: DBBoard = self.session.get(DBBoard, target_id)
        if not board.public and not self.pip.is_board_owner(board) and not self.pip.is_board_editor(board):
            raise EntityNotFound('board', 'id', target_id)
        
    def ensure_update(self, target_id): # Can change board information if they are the owner
        if self.pip.is_app_staff():
            return # staff users automatically get permissions
        self.ensure_read(target_id)
        board: DBBoard = self.session.get(DBBoard, target_id)
        if not self.pip.is_board_owner(board):
            raise NoPermissions("manage board", "board", target_id)
        
    def ensure_modify(self, target_id): # Can modify board if they are the owner or an editor
        if self.pip.is_app_staff():
            return # staff users automatically get permissions
        self.ensure_read(target_id)
        board: DBBoard = self.session.get(DBBoard, target_id)
        if not self.pip.is_board_owner(board) and not self.pip.is_board_editor(board):
            raise NoPermissions("modify board", "board", target_id)
        
    def ensure_delete(self, target_id): # Can delete a board if they are the owner
        if self.pip.is_app_staff():
            return # staff users automatically get permissions
        self.ensure_read(target_id)
        board: DBBoard = self.session.get(DBBoard, target_id)
        if not self.pip.is_board_owner(board):
            raise NoPermissions("delete board", "board", target_id)
        
    def ensure_view_editors(self, target_id): # Can view editors if they are an editor or owner
        if self.pip.is_app_staff():
            return # staff users automatically get permissions
        self.ensure_read(target_id)
        board: DBBoard = self.session.get(DBBoard, target_id)
        if not self.pip.is_board_owner(board) and not self.pip.is_board_editor(board):
            raise NoPermissions("view editors", "board", target_id)
        
    def ensure_manage_editors(self, target_id): # Can invite/remove editors if they are the owner
        if self.pip.is_app_staff():
            return # staff users automatically get permissions
        self.ensure_read(target_id)
        board: DBBoard = self.session.get(DBBoard, target_id)
        if not self.pip.is_board_owner(board):
            raise NoPermissions("manage editors", "board", target_id)
        
    def ensure_remove_editor(self, target_id, editor_id): # Can remove editors if they can manage editors, or if they're removing themself
        if self.account.id == editor_id:
            return
        self.ensure_manage_editors(target_id)

    def ensure_become_editor(self, target_id): # Can become an editor if they are not the owner
        board: DBBoard = self.session.get(DBBoard, target_id)
        if self.pip.is_board_owner(board):
            raise AddBoardOwnerAsEditor()
        
    def ensure_transfer(self, target_id): # Can transfer if they are the owner
        if self.pip.is_app_staff():
            return # staff users automatically get permissions
        self.ensure_read(target_id)
        board: DBBoard = self.session.get(DBBoard, target_id)
        if not self.pip.is_board_owner(board):
            raise NoPermissions("transfer board", "board", target_id)
        
    def ensure_become_owner(self, target_id): # Can become the owner if they can create boards and are an editor on this board
        self.ensure_create()
        board: DBBoard = self.session.get(DBBoard, target_id)
        if not self.pip.is_board_editor(board):
            raise InvalidOperation(f"Cannot transfer board with id={target_id} to account with id={self.account.id}")
        
# Dependencies

def get_board_pdp(
    session: DBSession, # type: ignore
    account: CurrentAccount,
) -> BoardPolicyDecisionPoint:
    return BoardPolicyDecisionPoint(session, account)
BoardPDP = Annotated[BoardPolicyDecisionPoint, Depends(get_board_pdp)]