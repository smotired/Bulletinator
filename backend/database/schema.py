"""Database table models."""

from sqlalchemy import (
    Integer, Float, String, Text, DateTime,
    ForeignKey, Table, Column,
    func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, declarative_base, validates
from typing import List, Optional
from uuid import uuid4
from datetime import datetime

Base = declarative_base()

def gen_uuid() -> str:
    # Function to generate a UUID string
    return str(uuid4())

# Intermediate table for many-to-many relationship between Accounts and the Boards they are allowed to edit
editor_table = Table(
    "editor_table",
    Base.metadata,
    Column("account_id", ForeignKey("accounts.id", ondelete="CASCADE")),
    Column("board_id", ForeignKey("boards.id", ondelete="CASCADE")),
)

class DBAccount(Base):
    """Accounts table. Each row represents an account account.

    Fields:
        - id: UUID primary key
        - username: unique identifier for account
        - display_name: Account display name 
        - email: the email associated with this account
        - hashed_password: the hashed password used to log in
        - profile_image: the src of the profile image (usually links to static directory, but backend should support links to any image)
        - created_at: the time at which this was created

    Relationships:
        - boards: Board, one-to-many
        - editable: Board, many-to-many
        - uploaded: Image, one-to-many
    """
    __tablename__ = "accounts"

    # fields
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: gen_uuid())
    username: Mapped[str] = mapped_column( String(64), unique=True, index=True )
    email: Mapped[str] = mapped_column( String(64), unique=True, index=True )
    display_name: Mapped[Optional[str]] = mapped_column( String(64), default=None )
    hashed_password: Mapped[str] = mapped_column( String(72), unique=True, index=True )
    profile_image: Mapped[Optional[str]] = mapped_column( String(120) )
    created_at: Mapped[datetime] = mapped_column( DateTime(), server_default=func.now() )

    # relationships
    boards: Mapped[List["DBBoard"]] = relationship( back_populates="owner", cascade="all, delete-orphan" ) # maybe later don't automatically delete unless they are the only editor
    editable: Mapped[List["DBBoard"]] = relationship( secondary=editor_table, back_populates="editors" )
    uploaded: Mapped[List["DBImage"]] = relationship( back_populates="uploader", cascade="all, delete-orphan", foreign_keys="DBImage.uploader_id" )

class DBBoard(Base):
    """Boards table. Each row represents a bulletin board.

    Fields:
        - id: UUID primary key
        - name: the name of the board
        - identifier: an alphanumeric board identifier, unique by username
        - icon: the string icon name that is being used
        - owner_id: the ID of the account that created the board.
            - deleting an account will cascade-delete boards
        - public: if the board can be viewed regardless of account
        - created_at: the time at which this was created

    Relationships:
        - owner: Account, many-to-one
        - editors: Account, many-to-many
        - items: Item, one-to-many
        - pins: Pin, one-to-many
    """
    
    __tablename__ = "boards"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: gen_uuid())
    identifier: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column( String(64) )
    icon: Mapped[str] = mapped_column( String(32), default="default" )
    owner_id: Mapped[int] = mapped_column( ForeignKey("accounts.id") )
    public: Mapped[bool] = mapped_column( default=False )
    created_at: Mapped[datetime] = mapped_column( DateTime(), server_default=func.now() )
    
    owner: Mapped["DBAccount"] = relationship( back_populates="boards" )
    editors: Mapped[List["DBAccount"]] = relationship( secondary=editor_table, back_populates="editable" )
    items: Mapped[List["DBItem"]] = relationship( back_populates="board", cascade="all, delete-orphan" )
    pins: Mapped[List["DBPin"]] = relationship( back_populates="board", cascade="all, delete-orphan", foreign_keys="DBPin.board_id" )

class DBItem(Base):
    """Items table. Each row represents an item.
    
    Fields:
        - id: UUID primary key
        - board_id: the id of the board this item is on
        - position: the position of this item on the board
        - list_id: the id of the list item this item may be in
        - index: the index of this item in a parent list
        - pin_id: the id of the pin that may be attached to this
        - type: the type of item
        - created_at: the time at which this was created
        - updated_at: the time at which this was last updated
        
    Relationships:
        - board: Board, many-to-one
        - list: List, many-to-one
        - pin: Pin, one-to-one
    """
    __tablename__ = "items"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: gen_uuid())
    board_id: Mapped[int] = mapped_column(ForeignKey("boards.id"))
    list_id: Mapped[Optional[int]] = mapped_column(ForeignKey("items_list.id"), default=None)
    position: Mapped[Optional[str]] # will be set conditionally
    index: Mapped[Optional[int]] # will be set conditionally
    pin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("pins.id"), default=None)
    type: Mapped[str] # used for polymorphism
    created_at: Mapped[datetime] = mapped_column( DateTime(), server_default=func.now() )
    updated_at: Mapped[datetime] = mapped_column( DateTime(), server_default=func.now() )
    
    board: Mapped["DBBoard"] = relationship(back_populates="items")
    list: Mapped["DBItemList"] = relationship(back_populates="contents", foreign_keys=[list_id])
    pin: Mapped[Optional["DBPin"]] = relationship( back_populates="item", cascade="all, delete-orphan", foreign_keys="DBPin.item_id" )
    
    __mapper_args__ = {
        "polymorphic_identity": "item",
        "polymorphic_on": "type"
    }
    
    def __repr__(self):
        return f"{self.__class__.__name__}({self.id})"
    
    # Set default values for position and index

    @validates("position")
    def validate_position(self, key, value):
        """If this item is in a list, it should not have a position."""
        if self.list_id is not None:
            return None
        return value or "0,0" # default to origin
    
    @validates("index")
    def validate_index(self, key, value):
        """If this item is not in a list, it should not have an index."""
        if self.list_id is None:
            return None
        if value is not None:
            return value
        if self.list:
            return len(self.list.contents) - 1
        return 0

class DBItemNote(DBItem):
    """Notes table. Each row represents a note item.
    
    Fields:
        - id: primary key - the id of the parent item
        - text: the markdown text of the note
        - size: the resized dimensions (overridden if in list)
    """
    __tablename__ = "items_note"
    
    id: Mapped[str] = mapped_column(ForeignKey("items.id"), primary_key=True)
    text: Mapped[str] = mapped_column(Text(300))
    size: Mapped[str] = mapped_column(default="300,200")
    
    __mapper_args__ = {
        "polymorphic_identity": "note",
    }

class DBItemLink(DBItem):
    """Links table. Each row represents a link item.
    
    Fields:
        - id: primary key - the id of the parent item
        - title: The text of the link
        - url: The URL of the link
    """
    __tablename__ = "items_link"
    
    id: Mapped[str] = mapped_column(ForeignKey("items.id"), primary_key=True)
    title: Mapped[str] = mapped_column( String(64) )
    url: Mapped[str] = mapped_column( String(128) )
    
    __mapper_args__ = {
        "polymorphic_identity": "link",
    }

class DBItemMedia(DBItem):
    """Media table. Each row represents a media item. Metdia items will typically
    be images, but maybe later we will support other types.
    
    Fields:
        - id: primary key - the id of the parent item
        - url: The link to the image, whether uploaded by the account or not.
        - size: The resized image size (overridden if in list)
    """
    __tablename__ = "items_media"
    
    id: Mapped[str] = mapped_column(ForeignKey("items.id"), primary_key=True)
    url: Mapped[str] = mapped_column( String(128) )
    size: Mapped[Optional[str]] = mapped_column(default=None)
    
    __mapper_args__ = {
        "polymorphic_identity": "media",
    }

class DBItemTodo(DBItem):
    """Todo list table. Each row represents a todo list item.
    
    Fields:
        - id: primary key - the id of the parent item
        - title: The title of the todo list

    Relationships:
        - contents: TodoItem, one-to-many. Ordered by TodoItem.id.
    """
    __tablename__ = "items_todo"
    
    id: Mapped[str] = mapped_column(ForeignKey("items.id"), primary_key=True)
    title: Mapped[str] = mapped_column( String(64) )
    
    contents: Mapped[List["DBTodoItem"]] = relationship(back_populates="todo", cascade="all, delete-orphan")
    
    __mapper_args__ = {
        "polymorphic_identity": "todo",
    }

class DBItemList(DBItem):
    """List table. Each row represents a list item.
    
    Fields:
        - id: primary key - the id of the parent item
        - title: The title of the list
        In the future we will have fields for sorting, etc.
        but not for the MVP.

    Relationships:
        - contents: Item, one-to-many.
    """
    __tablename__ = "items_list"
    
    id: Mapped[str] = mapped_column(ForeignKey("items.id"), primary_key=True)
    title: Mapped[str] = mapped_column( String(64) )
    
    contents: Mapped[List["DBItem"]] = relationship(back_populates="list", cascade="all, delete-orphan", foreign_keys="DBItem.list_id", order_by="DBItem.index")
    
    __mapper_args__ = {
        "polymorphic_identity": "list",
        "inherit_condition": id == DBItem.id  # specify the condition for inheritance
    }

class DBItemDocument(DBItem):
    """Document table. Each row represents a document item.
    
    Fields:
        - id: primary key - the id of the parent item
        - title: The title of the document
        - text: The text of the document

    Relationships:
        - contents: Item, one-to-many.
    """
    __tablename__ = "items_document"
    
    id: Mapped[str] = mapped_column(ForeignKey("items.id"), primary_key=True)
    title: Mapped[str] = mapped_column( String(64) )
    text: Mapped[str] = mapped_column( Text, default="" )
    
    __mapper_args__ = {
        "polymorphic_identity": "document",
        "inherit_condition": id == DBItem.id  # specify the condition for inheritance
    }

class DBTodoItem(Base):
    """Todo item table. Each row represents an item in a todo list item.
    
    Fields:
        - id: UUID primary key
        - list_id: the id of the containing todo list item
        - text: the short text representing this item
        - link: a link for this entry. can link to an item on this board.
        - done: true if this is checked off
        - created_at: the time at which this was created

    Relationships:
        - list: TodoList, many-to-one
    """
    __tablename__ = "todo_items"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: gen_uuid())
    list_id: Mapped[int] = mapped_column(ForeignKey("items_todo.id"))
    text: Mapped[str] = mapped_column( String(128) )
    link: Mapped[Optional[str]] = mapped_column( String(128), default=None)
    done: Mapped[bool]
    created_at: Mapped[datetime] = mapped_column( DateTime(), server_default=func.now() )
    
    todo: Mapped["DBItemTodo"] = relationship(back_populates="contents")

class DBImage(Base):
    """Image table. Each row represents an image that was uploaded.
    
    Fields:
        - uuid: uuid4 primary key
        - uploader_id: the account that uploaded this
        - filename: the name of the file on the server
        - created_at: the time at which this was created

    Relationships:
        - uploader: Account, many-to-one
    """
    __tablename__ = "images"
    
    uuid: Mapped[str] = mapped_column(String(36), primary_key=True, unique=True)
    uploader_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    filename: Mapped[str] = mapped_column( String(64) )
    uploaded_at: Mapped[datetime] = mapped_column( DateTime(), server_default=func.now() )
    
    uploader: Mapped["DBAccount"] = relationship(back_populates="uploaded", foreign_keys=[uploader_id])
    
class DBRefreshToken(Base):
    """Refresh token table. Each row represents a relationship between tokens and accounts.
    
    Fields:
        - token_id: the UUID of the token
        - account_id: the account the token belongs to
        - expires_at: the time at which this token should automatically expire
    """
    __tablename__ = "refresh_tokens"
    
    token_id: Mapped[str] = mapped_column(primary_key=True, unique=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    expires_at: Mapped[int]

# Intermediate table for many-to-many relationship between connected Pins
connection_table = Table(
    "connection_table",
    Base.metadata,
    Column("source_id", ForeignKey("pins.id", ondelete="CASCADE")),
    Column("destination_id", ForeignKey("pins.id", ondelete="CASCADE")),
)

class DBPin(Base):
    """Pin table. Each row represents a pin. Pins can attact to items, have labels, and connect to other pins.
    
    Fields:
        - id: UUID primary key
        - label: the label of the pin
        - compass: if the pin should be usable for navigation
        - board_id: The id of the Board containing this pin
        - item_id: The id of the Item this pin is attached to (optional)
        - created_at: the time at which this was created
    
    Relationships:
        - board: The Board containing this pin, many-to-one
        - item: The Item this pin is attached to, one-to-one
        - connections: The other Pins this Pin is attached to, many-to-many.
            - Bidirectional, so make sure to add and remove both directions at once.
    """
    __tablename__ = "pins"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: gen_uuid())
    label: Mapped[Optional[str]] = mapped_column( String(64) )
    compass: Mapped[bool] = mapped_column(default=False)
    board_id: Mapped[int] = mapped_column(ForeignKey("boards.id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    created_at: Mapped[datetime] = mapped_column( DateTime(), server_default=func.now() )
    
    board: Mapped["DBBoard"] = relationship(back_populates="pins", foreign_keys=[board_id])
    item: Mapped["DBItem"] = relationship(back_populates="pin", foreign_keys=[item_id])
    connections: Mapped[List["DBPin"]] = relationship(
        secondary=connection_table,
        primaryjoin=id == connection_table.c.source_id,
        secondaryjoin=id == connection_table.c.destination_id,
        back_populates="connections" )