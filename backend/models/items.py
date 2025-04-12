"""Request and response models for item functionality"""

from typing import Union, Optional
from pydantic import BaseModel
from backend.models import shared
from backend.database.schema import DBItem, DBItemNote, DBItemLink, DBItemMedia, DBItemTodo, DBItemList, DBItemDocument, DBTodoItem, DBPin

# Base Item

class Item(BaseModel):
    """Response model for an item"""
    id: str
    board_id: str
    list_id: str | None = None
    position: str | None = None
    index: int | None = None
    pin: Optional["Pin"] = None
    type: str
    
class ItemCollection(BaseModel):
    """Response model for a collection of items"""
    metadata: shared.Metadata
    items: list["SomeItem"]
    
class BaseItemCreate(BaseModel):
    """Basic request model for creating an item"""
    position: str | None = None # defaults to None if in a list and 0,0 otherwise
    list_id: str | None = None # defaults to None
    index: int | None = None # defaults to the end of a list if in a list and None otherwise
    type: str
    
class BaseItemUpdate(BaseModel):
    """Basic request model for updating an item"""
    position: str | None = None
    list_id: str | None = None
    index: int | None = None

class AllItemFields(BaseModel):
    """All fields available on all items, marked as optional, for use in request models."""
    text: str | None = None         # Note
    size: str | None = None         # Note, Media
    title: str | None = None        # Link, Todo, List
    url: str | None = None          # Link, Media

class ItemCreate(BaseItemCreate, AllItemFields):
    """Actual request model for creating an item. Contains required fields, as well as optional fields for the specific type of item.
    
    Should validate that relevant fields are included."""
    pass

class ItemUpdate(BaseItemUpdate, AllItemFields):
    """Actual request model for updating an item. Contains required fields, as well as optional fields for the specific type of item.
    
    Should validate that relevant fields are included."""
    pass
    
# Note Items
    
class ItemNote(Item):
    """Response model for a Note item"""
    text: str
    size: str
    
class ItemNoteCreate(BaseItemCreate):
    """Request model for creating a Note item"""
    text: str
    size: str = "300,400"
    
class ItemNoteUpdate(BaseItemUpdate):
    """Request model for updating a Note item"""
    text: str | None = None
    size: str | None = None
    
# Link Items
    
class ItemLink(Item):
    """Response model for a Link item"""
    title: str | None
    url: str
    
class ItemLinkCreate(BaseItemCreate):
    """Request model for creating a Link item"""
    title: str
    url: str
    
class ItemLinkUpdate(BaseItemUpdate):
    """Request model for updating a Link item"""
    title: str | None = None
    url: str | None = None
    
# Media Items
    
class ItemMedia(Item):
    """Response model for a Media item"""
    url: str
    size: str | None
    
class ItemMediaCreate(BaseItemCreate):
    """Request model for creating a Media item"""
    url: str
    size: str | None = None
    
class ItemMediaUpdate(BaseItemUpdate):
    """Request model for updating a Media item"""
    url: str | None = None
    size: str | None = None
    
# Todo Items
    
class ItemTodo(Item):
    """Response model for a Todo item"""
    title: str
    contents: "TodoItemCollection"
    
class ItemTodoCreate(BaseItemCreate):
    """Request model for creating a Todo item"""
    title: str
    
class ItemTodoUpdate(BaseItemUpdate):
    """Request model for updating a Todo item"""
    title: str | None = None
    
# List Items
    
class ItemList(Item):
    """Response model for a List item"""
    title: str
    contents: ItemCollection
    
class ItemListCreate(BaseItemCreate):
    """Request model for creating a List item"""
    title: str
    
class ItemListUpdate(BaseItemUpdate):
    """Request model for updating a List item"""
    title: str | None = None

# Document Items

class ItemDocument(Item):
    """Response model for a Document Item"""
    title: str
    text: str

class ItemDocumentCreate(BaseItemCreate):
    """Request model for creating a Document Item"""
    title: str
    text: str = ""

class ItemDocumentUpdate(BaseItemUpdate):
    """Request model for creating a Document Item"""
    title: str | None = None
    text: str | None = None
    
# Items within a todo list

class TodoItem(BaseModel):
    """Response model for an item in a todo list"""
    id: str
    list_id: str
    text: str
    link: str | None = None
    done: bool

class TodoItemCollection(BaseModel):
    """Response model for a group of todo list items"""
    metadata: shared.Metadata
    items: list[TodoItem]

# Pins that can connect different items

class Pin(BaseModel):
    """Response model for a pin"""
    id: str
    board_id: str
    item_id: str
    label: str | None = None
    compass: bool
    connections: list[str] # not a pin collection because of the infinite recursion

class PinCreate(BaseModel):
    """Request model for creating a pin"""
    item_id: str
    label: str | None = None
    compass: bool = False

class PinUpdate(BaseModel):
    """Request model for updating a pin"""
    item_id: str | None = None
    label: str | None = None
    compass: bool | None = None

# Union of all item types
SomeItem = Union[ItemNote, ItemLink, ItemMedia, ItemTodo, ItemList, ItemDocument]

# List-related request models (both List items and Todo items)

class TodoItemCreate(BaseModel):
    """Request model for adding to a todo list"""
    list_id: str
    text: str
    link: str | None = None
    done: bool = False
    
class TodoItemUpdate(BaseModel):
    """Request model for updating a todo list item"""
    text: str | None = None
    link: str | None = None
    done: bool | None = None

# Fields for base item
ITEMFIELDS = [ "board_id", "list_id", "position", "index", "type" ]
# Mappings from type strings to various subclasses, and required fields.
ITEMTYPES: dict[str, dict[str, type | list[str]]] = {
    "note": { "base": ItemNote, "db": DBItemNote, "create": ItemNoteCreate, "update": ItemNoteUpdate, "required_fields": [ "text" ] },
    "link": { "base": ItemLink, "db": DBItemLink, "create": ItemLinkCreate, "update": ItemLinkUpdate, "required_fields": [ "title", "url" ] },
    "media": { "base": ItemMedia, "db": DBItemMedia, "create": ItemMediaCreate, "update": ItemMediaUpdate, "required_fields": [ "url" ] },
    "todo": { "base": ItemTodo, "db": DBItemTodo, "create": ItemTodoCreate, "update": ItemTodoUpdate, "required_fields": [ "title" ] },
    "list": { "base": ItemList, "db": DBItemList, "create": ItemListCreate, "update": ItemListUpdate, "required_fields": [ "title" ] },
    "document": { "base": ItemDocument, "db": DBItemDocument, "create": ItemDocumentCreate, "update": ItemDocumentUpdate, "required_fields": [ "title" ] }
}

def convert_item(db_item: DBItem) -> SomeItem:
    item_type = ITEMTYPES.get(db_item.type, { "base": Item })['base']
    # Convert collections before validating
    db_dict = db_item.__dict__
    db_dict['pin'] = convert_pin( db_item.pin ).__dict__ if db_item.pin else None
    if item_type == ItemTodo:
        collection = TodoItemCollection(
            metadata=shared.Metadata(count=len(db_item.contents)),
            items=convert_todo_item_list(db_item.contents)
        )
        item_dict = Item.model_validate(db_dict).model_dump()
        item_dict['title'] = db_item.title
        item_dict['contents'] = collection
        return ItemTodo(**item_dict)
    if item_type == ItemList:
        collection = ItemCollection(
            metadata=shared.Metadata(count=len(db_item.contents)),
            items=convert_item_list(db_item.contents) # no need to worry about recursion because lists cannot contain other lists
        )
        item_dict = Item.model_validate(db_dict).model_dump()
        item_dict['title'] = db_item.title
        item_dict['contents'] = collection
        return ItemList(**item_dict)
    # Otherwise we can just validate
    return item_type.model_validate(db_dict)

def convert_item_list(db_items: list[DBItem]) -> list[SomeItem]:
    return [ convert_item(db_item) for db_item in db_items ]

def convert_todo_item(todo_item: DBTodoItem) -> TodoItem:
    return TodoItem.model_validate(todo_item.__dict__)

def convert_todo_item_list(todo_items: list[DBTodoItem]) -> list[TodoItem]:
    return [ convert_todo_item(item) for item in todo_items ]

def convert_pin(db_pin: DBPin) -> Pin:
    return Pin(
        id=db_pin.id,
        board_id=db_pin.board_id,
        item_id=db_pin.item_id,
        label=db_pin.label,
        compass=db_pin.compass,
        connections=[ other.id for other in db_pin.connections ]
    )