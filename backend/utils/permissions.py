"""Functionality for permissions"""

from abc import ABC as AbstractBaseClass, abstractmethod
from fastapi import Depends
from typing import Annotated

from sqlalchemy import select, func

from backend.config import settings
from backend.dependencies import DBSession, CurrentAccount
from backend.database.schema import DBAccount, DBBoard, DBReport, DBItem
from backend.exceptions import *

# Every item type in this list is considered a premium feature
PREMIUM_TYPES = [ "document" , "sketch", "latex", "kanban", "widget" ] # some of these are just planned

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
    
    def is_report_submitter(self, target: DBReport | str) -> bool:
        report: DBReport = target if isinstance(target, DBReport) else self.session.get(DBReport, target)
        return report is not None and self.account.id == report.account_id
    
    def is_report_assignee(self, target: DBReport | str) -> bool:
        if not self.is_app_staff():
            return False
        report: DBReport = target if isinstance(target, DBReport) else self.session.get(DBReport, target)
        return report is not None and self.account.id == report.moderator_id
    
    def is_premium(self) -> bool:
        return self.account.customer is not None and self.account.customer.type in [ "active", "inactive", "lifetime" ]
    
    def created_item_count(self) -> int:
        """Gets the total amount of items on all boards owned by this user"""
        statement = select(func.count(DBItem.id)).join(DBBoard, DBItem.board_id == DBBoard.id).where(DBBoard.owner_id == self.account.id)
        return self.session.execute(statement).scalar()
    
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

class AccountPolicyDecisionPoint(PolicyDecisionPoint):
    """Handles permissions for accounts"""
    def ensure_create(self): # Anyone can create a user
        pass

    def ensure_read_all(self): # Only staff can see all users
        if not self.pip.is_app_staff():
            raise NoPermissions("view all accounts", "account", self.account.id)

    def ensure_read(self, target_id): # Can always view a specific user
        pass

    def ensure_update(self, target_id): # Must be the account owner
        if self.account.id != target_id:
            raise NoPermissions("update account", "account", self.account.id)

    def ensure_delete(self, target_id): # Must be the account owner or a staff member
        if self.account.id != target_id and not self.pip.is_app_staff():
            raise NoPermissions("delete account", "account", self.account.id)

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
        if board is None:
            raise EntityNotFound('board', 'id', target_id)
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
        
    def ensure_create_item(self, target_id: str, target_type: str): # Calls can_modify and has additional checks for premium features
        self.ensure_modify(target_id)
        # Create a PDP for the board owner
        board: DBBoard = self.session.get(DBBoard, target_id)
        owner = BoardPolicyDecisionPoint(self.session, board.owner)
        if not owner.pip.is_premium():
            if target_type in PREMIUM_TYPES:
                raise PremiumFeature()
            if owner.pip.created_item_count() >= settings.free_tier_item_limit:
                raise ItemLimitExceeded() 
        
    def ensure_update_item(self, target_id: str, target_type: str): # Calls can_modify and has additional checks for premium features
        self.ensure_modify(target_id)
        # Create a PDP for the board owner
        board: DBBoard = self.session.get(DBBoard, target_id)
        owner = BoardPolicyDecisionPoint(self.session, board.owner)
        if not owner.pip.is_premium():
            if target_type in PREMIUM_TYPES:
                raise PremiumFeature()
        
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
        
    def ensure_reference(self, target_id): # Can reference this board when creating a new board if they are an editor or owner on this board
        if self.pip.is_app_staff():
            return # staff users automatically get permissions
        self.ensure_read(target_id)
        board: DBBoard = self.session.get(DBBoard, target_id)
        if not self.pip.is_board_owner(board) and not self.pip.is_board_editor(board):
            raise NoPermissions("reference board", "board", target_id)

class ReportPolicyDecisionPoint(PolicyDecisionPoint):
    """Handles permissions for user reports"""
    def ensure_create(self): # Anyone can create a report
        pass

    def ensure_read_all(self): # Only staff can see all reports
        if not self.pip.is_app_staff():
            raise NoPermissions("view all accounts", "account", self.account.id)

    def ensure_query_all(self): # Anyone can ask for a list of reports and should only see the ones they've submitted.
        pass

    def ensure_read(self, target_id): # Can view a specific report if you submitted it or are a staff member
        if self.pip.is_app_staff():
            return # staff users automatically get permissions
        if not self.pip.is_report_submitter(target_id):
            raise EntityNotFound('report', 'id', target_id)

    def ensure_update(self, target_id): # To update basic information, be the report submitter
        if not self.pip.is_report_submitter(target_id):
            if self.pip.is_app_staff():
                raise NoPermissions('update report', 'report', target_id)
            raise EntityNotFound('report', 'id', target_id)
        
    def ensure_update_status(self, target_id): # To update status must be assignee
        if not self.pip.is_report_assignee(target_id):
            if not self.pip.is_app_staff() and not self.pip.is_report_submitter(target_id):
                raise EntityNotFound('report', 'id', target_id)
            raise NoPermissions('update report status', 'report', target_id)

    def ensure_delete(self, target_id): # Must be the account owner or a staff member
        report: DBReport | None = self.session.get(DBReport, target_id)
        if report is None:
            raise EntityNotFound("report", "id", target_id)
        if self.account.id != report.account_id and not self.pip.is_app_staff():
            raise EntityNotFound("report", "id", target_id)
        
    def ensure_manage_assignee(self, target_id): # Must be a staff member
        if not self.pip.is_app_staff():
            if not self.pip.is_report_submitter(target_id):
                raise EntityNotFound('report', 'id', target_id)
            raise NoPermissions('manage assignee', 'report', target_id)
        
    def ensure_become_assignee(self, target_id): # Must be a staff member
        if not self.pip.is_app_staff():
            raise NoPermissions('become assignee', 'report', target_id)
        
# Dependencies

def get_account_pdp(
    session: DBSession, # type: ignore
    account: CurrentAccount,
) -> AccountPolicyDecisionPoint:
    return AccountPolicyDecisionPoint(session, account)
AccoutPDP = Annotated[AccountPolicyDecisionPoint, Depends(get_account_pdp)]

def get_board_pdp(
    session: DBSession, # type: ignore
    account: CurrentAccount,
) -> BoardPolicyDecisionPoint:
    return BoardPolicyDecisionPoint(session, account)
BoardPDP = Annotated[BoardPolicyDecisionPoint, Depends(get_board_pdp)]

def get_report_pdp(
    session: DBSession, # type: ignore
    account: CurrentAccount,
) -> ReportPolicyDecisionPoint:
    return ReportPolicyDecisionPoint(session, account)
ReportPDP = Annotated[ReportPolicyDecisionPoint, Depends(get_report_pdp)]