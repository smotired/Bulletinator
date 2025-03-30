"""Request and response models for item functionality"""

from typing import Union
from pydantic import BaseModel
from backend.models import shared
from backend.database.schema import DBItem, DBItemNote, DBItemLink, DBItemMedia, DBItemTodo, DBItemList, DBTodoItem

# Base Item

class Item(BaseModel):
    """Response model for an item"""
    id: int
    board_id: int
    list_id: int | None = None
    position: str | None = None
    index: int | None = None
    type: str
    
class ItemCollection(BaseModel):
    """Response model for a collection of items"""
    metadata: shared.Metadata
    items: list["SomeItem"]
    
class BaseItemCreate(BaseModel):
    """Basic request model for creating an item"""
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

# Union of all item types
SomeItem = Union[ItemNote, ItemLink, ItemMedia, ItemTodo, ItemList]

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

def convert_item(db_item: DBItem) -> Item:
    item_type = item_type_mapping.get(type(db_item), Item)
    # Convert collections before validating
    if item_type == ItemTodo:
        collection = TodoItemCollection(
            metadata=shared.Metadata(count=len(db_item.contents)),
            items=convert_todo_item_list(db_item.contents)
        )
        item_dict = Item.model_validate(db_item.__dict__).model_dump()
        item_dict['title'] = db_item.title
        item_dict['contents'] = collection
        return ItemTodo(**item_dict)
    if item_type == ItemList:
        print([ i.__dict__ for i in db_item.contents ])
        collection = ItemCollection(
            metadata=shared.Metadata(count=len(db_item.contents)),
            items=convert_item_list(db_item.contents) # no need to worry about recursion because lists cannot contain other lists
        )
        item_dict = Item.model_validate(db_item.__dict__).model_dump()
        item_dict['title'] = db_item.title
        item_dict['contents'] = collection
        return ItemList(**item_dict)
    # Otherwise we can just validate
    return item_type.model_validate(db_item.__dict__)

def convert_item_list(db_items: list[DBItem]) -> list[SomeItem]:
    return [ convert_item(db_item) for db_item in db_items ]

def convert_todo_item(todo_item: DBTodoItem) -> TodoItem:
    return TodoItem.model_validate(todo_item.__dict__)

def convert_todo_item_list(todo_items: list[DBTodoItem]) -> list[TodoItem]:
    return [ convert_todo_item(item) for item in todo_items ]