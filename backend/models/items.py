"""Request and response models for item functionality"""

from pydantic import BaseModel
from backend.models import shared
from backend.database.schema import DBItem, DBItemNote, DBItemLink, DBItemMedia, DBItemTodo, DBItemList

# Base Item

class Item(BaseModel):
    """Response model for an item"""
    id: int
    item_id: int
    position: str
    list_id: int | None = None
    index: int | None = None
    type: str
    
class ItemCollection(BaseModel):
    """Response model for a collection of items"""
    metadata: shared.Metadata
    items: list[Item]
    
class BaseItemCreate(BaseModel):
    """Basic request model for creating an item"""
    item_id: int
    position: str
    list_id: int | None = None
    index: int | None = None
    type: str
    
class BaseItemUpdate(BaseModel):
    """Basic request model for updating an item"""
    position: str | None = None
    list_id: int | None = None
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
    title: str | None
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
    
# Items within a todo list

class TodoItem(BaseModel):
    """Request model for an item in a todo list"""
    id: int
    list_id: int
    text: str
    link: str | None
    done: bool

class TodoItemCollection(BaseModel):
    """Request model for a group of todo list items"""
    metadata: shared.Metadata
    items: list[TodoItem]

# List-related request models (both List items and Todo items)

class TodoAdd(BaseModel):
    """Request model for adding to a todo list"""
    todo_id: int
    text: str
    link: str | None
    
class TodoRemove(BaseModel):
    """Request model for removing from a todo list"""
    todo_id: int
    index: int
    
class TodoComplete(BaseModel):
    """Request model for checking off in a todo list"""
    todo_id: int
    index: int

class ItemListInsert(BaseModel):
    """Request model for inserting an existing item into a list"""
    item_id: int
    list_id: int
    index: int
    
class ItemListRemove(BaseModel):
    """Request model for removing an item from a list"""
    list_id: int
    item_id: int | None = None # removing the item
    index: int | None = None # removing the item at an index

class ItemIndexChange(BaseModel):
    """Request model for changing the index of an item within a List item"""
    id: int # the id of the item
    new_index: int | None = None # setting an exact index
    index_offset: int | None = None # setting a relative index

# Mappings from DBItem subclasses to Item subclasses.
item_type_mapping = {
    DBItemNote: ItemNote,
    DBItemLink: ItemLink,
    DBItemMedia: ItemMedia,
    DBItemTodo: ItemTodo,
    DBItemList: ItemList,
}

def convert_item(db_item: DBItem):
    item_type = item_type_mapping.get(type(db_item), Item)
    return item_type.model_validate(db_item.__dict__)

def convert_item_list(db_items: list[DBItem]):
    return [ convert_item(db_item) for db_item in db_items ]