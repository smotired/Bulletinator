"""Database table models."""

from sqlmodel import Field, Relationship, SQLModel

class DBUser(SQLModel, table=True):
    """Users table. Each row represents a user account.

    Fields:
        - id: primary key (auto-increments)
        - username: unique identifier for account
        - email: the email associated with this account
        - hashed_password: the hashed password used to log in
        - profile_image_id: the id of the profile image

    Relationships:
        - boards: Board, one-to-many
    """

    __tablename__ = "users" # type: ignore

    # fields
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    profile_image_id: int | None = Field(default=None)

    # relationships
    boards: list["DBBoard"] = Relationship(
        back_populates="owner",
        cascade_delete=True,
    )

class DBBoard(SQLModel, table=True):
    """Boards table. Each row represents a bulletin board.

    Fields:
        - id: primary key (auto-increments)
        - name: the name of the board
        - icon: the string icon name that is being used
        - owner_id: the ID of the user that created the board.
            - deleting a user will cascade-delete boards
        - public: if the board can be viewed regardless of account

    Relationships:
        - owner: User, many-to-one
        - editors: Editor, one-to-many
        - items: Item, one-to-many
    """

class DBEditor(SQLModel, table=True):
    """Editors table. Each row represents a relationship between
    a user and a board, where the user is allowed to edit that board.
    Owner accounts are always allowed to edit, and should not have a record here.

    Fields:
        - user_id: primary_key, the id of the editor user
        - board_id: primary_key, the id of the board

    Relationships:
        - editor is a many-to-many relationship between users and boards
    """

class DBItem(SQLModel, table=True):
    """Items table. Each row represents an item.
    
    Fields:
        - id: primary key (auto-increments)
        - board_id: the id of the board this item is on
        - list_id: the id of the list item this item may be in
        - position: the position of this item on the board
        - index: the index of this item in a parent list
        - type: the type of item
        
    Relationships:
        - board: Board, many-to-one
        - list: List, many-to-one
        - item: Some subclass of Item, one-to-one
    """

class DBNote(DBItem, table=True):
    """Notes table. Each row represents a note item.
    
    Fields:
        - item_id: primary key - the id of the parent item
        - text: the markdown text of the note
        - size: the resized dimensions (overridden if in list)

    Relationships:
        - item: Item, one-to-one
    """

class DBLink(DBItem, table=True):
    """Links table. Each row represents a link item.
    
    Fields:
        - item_id: primary key - the id of the parent item
        - text: The text of the link
        - url: The URL of the link

    Relationships:
        - item: Item, one-to-one
    """

class DBImage(DBItem, table=True):
    """Images table. Each row represents an image item.
    
    Fields:
        - item_id: primary key - the id of the parent item
        - image_id: The ID of the uploaded image
        - size: The resized image size (overridden if in list)

    Relationships:
        - item: Item, one-to-one
        - image: UplaodedImage, many-to-one
    """

class DBTodoList(DBItem, table=True):
    """Todo list table. Each row represents a todo list item.
    
    Fields:
        - item_id: primary key - the id of the parent item
        - title: The title of the todo list

    Relationships:
        - item: Item, one-to-one
        - contents: TodoItem, one-to-many. Ordered by TodoItem.id.
    """

class DBList(DBItem, table=True):
    """List table. Each row represents a list item.
    
    Fields:
        - item_id: primary key - the id of the parent item
        - title: The title of the list
        In the future we will have fields for sorting, etc.
        but not for the MVP.

    Relationships:
        - item: Item, one-to-one
        - contents: Item, one-to-many.
    """

class DBTodoItem(DBItem, table=True):
    """Todo item table. Each row represents an item in a todo list item.
    
    Fields:
        - id: primary key (auto-increments)
        - list_id: the id of the containing todo list item
        - text: the short text representing this item
        - link: a link for this entry. can link to an item on this board.
        - done: true if this is checked off

    Relationships:
        - item: Item, one-to-one
        - list: TodoList, many-to-one
    """

class DBUploadedImage(DBItem, table=True):
    """Uploaded image table. Each row represents an image that was uploaded.
    
    Fields:
        - id: primary key (auto-increments)
        - uploader_id: the user that uploaded this
        - filename: the name of the file on the server

    Relationships:
        - uploader: User, many-to-one
    """