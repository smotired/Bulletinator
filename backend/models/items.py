"""Request and response models for item functionality"""

from pydantic import BaseModel
import shared

# Base Item

class Item(BaseModel):
    """Response model for an item"""
    id: int
    board_id: int
    position: str
    list_id: int | None = None
    index: int | None = None
    type: str
    
class ItemCollection(BaseModel):
    """Response model for a collection of items"""
    metadata: shared.Metadata
    boards: list[Item]
    
class ItemCreate(BaseModel):
    """Request model for creating an item"""
    board_id: int
    position: str
    list_id: int | None = None
    index: int | None = None
    
class ItemUpdate(BaseModel):
    """Request model for updating an item"""
    position: str | None = None
    list_id: int | None = None
    index: int | None = None
    
# Note Items
    
class ItemNote(Item):
    """Response model for a Note item"""
    text: str
    size: str
    
class ItemNoteCreate(Item):
    """Request model for creating a Note item"""
    text: str
    size: str = "300,400"
    
class ItemNoteUpdate(Item):
    """Request model for updating a Note item"""
    text: str | None = None
    size: str | None = None
    
# Link Items
    
class ItemLink(Item):
    """Response model for a Link item"""
    title: str | None
    url: str
    
class ItemLinkCreate(Item):
    """Request model for creating a Link item"""
    title: str | None
    url: str
    
class ItemLinkUpdate(Item):
    """Request model for updating a Link item"""
    title: str | None = None
    url: str | None = None
    
# Media Items
    
class ItemMedia(Item):
    """Response model for a Media item"""
    src: str
    size: str | None
    
class ItemMediaCreate(Item):
    """Request model for creating a Media item"""
    src: str
    size: str | None = None
    
class ItemMediaUpdate(Item):
    """Request model for updating a Media item"""
    src: str | None = None
    size: str | None = None
    
# Todo Items
    
class ItemTodo(Item):
    """Response model for a Todo item"""
    title: str
    contents: "TodoItemCollection"
    
class ItemTodoCreate(Item):
    """Request model for creating a Todo item"""
    title: str
    
class ItemTodoUpdate(Item):
    """Request model for updating a Todo item"""
    title: str | None = None
    
# List Items
    
class ItemList(Item):
    """Response model for a List item"""
    title: str
    contents: ItemCollection
    
class ItemListCreate(Item):
    """Request model for creating a List item"""
    title: str
    
class ItemListUpdate(Item):
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