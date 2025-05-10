"""Request and response models for item functionality"""

from typing import Union, Optional, Callable, Any
from pydantic import BaseModel, model_validator
from backend.models.shared import Metadata, Collection, CollectionFactory
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
    
class BaseItemCreate(BaseModel):
    """Basic request model for creating an item"""
    position: str | None = None # defaults to None if in a list and 0,0 otherwise
    list_id: str | None = None # defaults to None
    index: int | None = None # defaults to the end of a list if in a list and None otherwise
    type: str
    
class BaseItemUpdate(BaseModel):
    """Basic request model for updating an item"""
    board_id: str | None = None
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
    
class ItemNoteCreate(BaseItemCreate):
    """Request model for creating a Note item"""
    text: str
    
class ItemNoteUpdate(BaseItemUpdate):
    """Request model for updating a Note item"""
    text: str | None = None
    
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
    items: "Collection[TodoItem]"
    
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
    items: "ItemCollection"
    
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

# Pins that can connect different items

class Pin(BaseModel):
    """Response model for a pin"""
    id: str
    board_id: str
    item_id: str
    label: str | None = None
    compass: bool
    connections: list[str] # not a pin collection because of the infinite recursion

    @model_validator(mode='before')
    @classmethod
    def convert_from_db_pin(cls, obj: Any) -> Any:
        """Converts a DBPin"""
        if not isinstance(obj, DBPin):
            return obj
        pin_connections = [ other.id for other in obj.connections ]
        duplicate = obj.__dict__.copy()
        duplicate['connections'] = pin_connections
        return Pin(
            **duplicate,
        ).model_dump()

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

# Converters from item types with special fields (like references to other items)
ITEM_CONVERTERS: dict[type, Callable[[DBItem], Item]] = {}

# Decorator that maps these converter functions
def register_item_converter(model_type: type):
    def wrapper(func: Callable[[DBItem, dict], model_type]): # type: ignore
        ITEM_CONVERTERS[model_type] = func
        return func
    return wrapper

# Converter functions for specific item types

@register_item_converter(ItemTodo)
def convert_todo(todo: DBItemTodo, d: dict) -> ItemTodo:
    collection = CollectionFactory(TodoItem, DBTodoItem).model_validate(todo.contents).model_dump()
    item_dict = Item.model_validate(d).model_dump()
     # Apply type-specific fields and then return
    item_dict['title'] = todo.title
    item_dict['items'] = collection
    return ItemTodo(**item_dict)

@register_item_converter(ItemList)
def convert_list(list: DBItemList, d: dict) -> ItemList:
    collection = ItemCollection.model_validate(list.contents).model_dump()
    item_dict = Item.model_validate(d).model_dump()
     # Apply type-specific fields and then return
    item_dict['title'] = list.title
    item_dict['items'] = collection
    return ItemList(**item_dict)

# Main manual converter
def convert_item(db_item: DBItem) -> SomeItem:
    item_type = ITEMTYPES.get(db_item.type, { "base": Item })['base']
    # Convert pin before validating
    db_dict = db_item.__dict__
    db_dict['pin'] = Pin.model_validate(db_item.pin).model_dump() if db_item.pin else None
    # Handle special conversions
    if item_type in ITEM_CONVERTERS:
        return ITEM_CONVERTERS[item_type](db_item, db_dict)
    # Otherwise we can just validate
    return item_type.model_validate(db_dict)

# Items require their own collection due to polymorphism
class ItemCollection(BaseModel):
    """Response model for an item collection."""

    metadata: Metadata
    contents: list[SomeItem]

    @model_validator(mode='before')
    @classmethod
    def convert_item_list(cls, obj: Any) -> Any:
        """Constructs a collection from a list of DBItems"""
        if isinstance(obj, list):
            # Make sure either the list is empty or everything matches this type
            if not all([ isinstance(x, DBItem) for x in obj ]):
                return obj
            # If this is indeed a list[DBItem] create the equivalent of a a Collection[ContentsType] from these items
            return ItemCollection(
                metadata=Metadata( count=len(obj) ),
                contents=[ convert_item(element) for element in obj ]
            ).model_dump()
        return obj