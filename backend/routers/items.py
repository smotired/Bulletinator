"""Router for board item routes.

Args:
    router (APIRouter): Router for /boards/{board_id}/items routes
"""

from fastapi import APIRouter

from backend.database.schema import *
from backend.database import items as items_db
from backend.dependencies import DBSession, CurrentAccount, OptionalAccount
from backend.models.items import *
from backend.models.shared import Metadata

router = APIRouter(prefix="/boards/{board_id}/items", tags=["Item"])

@router.get("/", status_code=200)
def get_items(
    session: DBSession, # type: ignore
    board_id: int,
    account: OptionalAccount
) -> ItemCollection:
    """If the current account can see the board with this ID, return a collection of all items on this board."""
    items = items_db.get_items(session, board_id, account)
    return ItemCollection(
        metadata=Metadata(count=len(items)),
        items=convert_item_list( items )
    )

@router.get("/{item_id}", status_code=200)
def get_item(
    session: DBSession, # type: ignore
    board_id: int,
    item_id: int,
    account: OptionalAccount
) -> SomeItem:
    """If the account can edit this board, add an item."""
    return convert_item( items_db.get_item(session, board_id, item_id, account) )

@router.post("/", status_code=201)
def add_item(
    session: DBSession, # type: ignore
    board_id: int,
    config: ItemCreate,
    account: CurrentAccount
) -> SomeItem:
    """If the account can edit this board, add an item."""
    return convert_item( items_db.create_item(session, board_id, config, account) )

@router.put("/{item_id}", status_code=200)
def update_item(
    session: DBSession, # type: ignore
    board_id: int,
    item_id: int,
    config: ItemUpdate,
    account: CurrentAccount
) -> SomeItem:
    """Updates an item on this board."""
    return convert_item( items_db.update_item(session, board_id, item_id, config, account) )

@router.delete("/{item_id}", status_code=204)
def delete_item(
    session: DBSession, # type: ignore
    board_id: int,
    item_id: int,
    account: CurrentAccount
) -> None:
    """Deletes an item on this board."""
    items_db.delete_item(session, board_id, item_id, account)

@router.post("/todo", status_code=201)
def add_todo_item(
    session: DBSession, # type: ignore
    board_id: int,
    config: TodoItemCreate,
    account: CurrentAccount
) -> TodoItem:
    """Add an item to a todo list on this board."""
    return items_db.create_todo_item(session, board_id, config, account)

@router.put("/todo/{todo_item_id}", status_code=200)
def update_todo_item(
    session: DBSession, # type: ignore
    board_id: int,
    todo_item_id: int,
    config: TodoItemUpdate,
    account: CurrentAccount
) -> TodoItem:
    """Updates an item in a todo list on this board."""
    return items_db.update_todo_item(session, board_id, todo_item_id, config, account)

@router.delete("/todo/{todo_item_id}", status_code=204)
def delete_todo_item(
    session: DBSession, # type: ignore
    board_id: int,
    todo_item_id: int,
    account: CurrentAccount
) -> None:
    """Add an item to a todo list on this board."""
    items_db.delete_todo_item(session, board_id, todo_item_id, account)

@router.put("/pins/connect", status_code=200)
def connect_pin(
    session: DBSession, # type: ignore
    board_id: int,
    p1: int,
    p2: int,
    account: CurrentAccount
) -> list[Pin]:
    """Adds a connection between two pins on this board."""
    return [ convert_pin(pin) for pin in items_db.add_pin_connection(session, board_id, p1, p2, account) ]

@router.delete("/pins/connect", status_code=200)
def disconnect_pin(
    session: DBSession, # type: ignore
    board_id: int,
    p1: int,
    p2: int,
    account: CurrentAccount
) -> list[Pin]:
    """Deletes a connection between two pins on this board."""
    return [ convert_pin(pin) for pin in items_db.remove_pin_connection(session, board_id, p1, p2, account) ]

@router.post("/pins", status_code=201)
def create_pin(
    session: DBSession, # type: ignore
    board_id: int,
    config: PinCreate,
    account: CurrentAccount
) -> Pin:
    """Creates a pin on this board."""
    return convert_pin( items_db.create_pin(session, board_id, config, account) )

@router.put("/pins/{pin_id}", status_code=200)
def update_pin(
    session: DBSession, # type: ignore
    board_id: int,
    pin_id: int,
    config: PinUpdate,
    account: CurrentAccount
) -> Pin:
    """Updates a pin on this board."""
    return convert_pin( items_db.update_pin(session, board_id, pin_id, config, account) )

@router.delete("/pins/{pin_id}", status_code=204)
def delete_pin(
    session: DBSession, # type: ignore
    board_id: int,
    pin_id: int,
    account: CurrentAccount
):
    """Deletes a pin on this board."""
    items_db.delete_pin(session, board_id, pin_id, account)