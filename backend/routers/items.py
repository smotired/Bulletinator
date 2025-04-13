"""Router for board item routes.

Args:
    router (APIRouter): Router for /boards/{board_id}/items routes
"""

from fastapi import APIRouter
from uuid import UUID

from backend.database.schema import *
from backend.database import items as items_db
from backend.dependencies import DBSession, CurrentAccount, OptionalAccount
from backend.permissions import BoardPDP
from backend.models.items import *
from backend.models.shared import Metadata

router = APIRouter(prefix="/boards/{board_id}/items", tags=["Item"])

@router.get("/", status_code=200)
def get_items(
    session: DBSession, # type: ignore
    board_id: UUID,
    account: OptionalAccount
) -> ItemCollection:
    """If the current account can see the board with this ID, return a collection of all items on this board."""
    items = items_db.get_items(session, str(board_id), account)
    return ItemCollection(
        metadata=Metadata(count=len(items)),
        items=convert_item_list( items )
    )

@router.get("/{item_id}", status_code=200)
def get_item(
    session: DBSession, # type: ignore
    board_id: UUID,
    item_id: UUID,
    account: OptionalAccount
) -> SomeItem:
    """If the account can edit this board, add an item."""
    return convert_item( items_db.get_item(session, str(board_id), str(item_id), account) )

@router.post("/", status_code=201)
def add_item(
    session: DBSession, # type: ignore
    pdp: BoardPDP,
    board_id: UUID,
    config: ItemCreate,
) -> SomeItem:
    """If the account can edit this board, add an item."""
    return convert_item( items_db.create_item(session, pdp, str(board_id), config) )

@router.put("/{item_id}", status_code=200)
def update_item(
    session: DBSession, # type: ignore
    pdp: BoardPDP,
    board_id: UUID,
    item_id: UUID,
    config: ItemUpdate,
) -> SomeItem:
    """Updates an item on this board."""
    return convert_item( items_db.update_item(session, pdp, str(board_id), str(item_id), config) )

@router.delete("/{item_id}", status_code=204)
def delete_item(
    session: DBSession, # type: ignore
    pdp: BoardPDP,
    board_id: UUID,
    item_id: UUID,
) -> None:
    """Deletes an item on this board."""
    items_db.delete_item(session, pdp, str(board_id), str(item_id))

@router.post("/todo", status_code=201)
def add_todo_item(
    session: DBSession, # type: ignore
    pdp: BoardPDP,
    board_id: UUID,
    config: TodoItemCreate,
) -> TodoItem:
    """Add an item to a todo list on this board."""
    return items_db.create_todo_item(session, pdp, str(board_id), config)

@router.put("/todo/{todo_item_id}", status_code=200)
def update_todo_item(
    session: DBSession, # type: ignore
    pdp: BoardPDP,
    board_id: UUID,
    todo_item_id: UUID,
    config: TodoItemUpdate,
) -> TodoItem:
    """Updates an item in a todo list on this board."""
    return items_db.update_todo_item(session, pdp, str(board_id), str(todo_item_id), config)

@router.delete("/todo/{todo_item_id}", status_code=204)
def delete_todo_item(
    session: DBSession, # type: ignore
    pdp: BoardPDP,
    board_id: UUID,
    todo_item_id: UUID,
) -> None:
    """Add an item to a todo list on this board."""
    items_db.delete_todo_item(session, pdp, str(board_id), str(todo_item_id))

@router.put("/pins/connect", status_code=200)
def connect_pin(
    session: DBSession, # type: ignore
    pdp: BoardPDP,
    board_id: UUID,
    p1: UUID,
    p2: UUID,
) -> list[Pin]:
    """Adds a connection between two pins on this board."""
    return [ convert_pin(pin) for pin in items_db.add_pin_connection(session, pdp, str(board_id), str(p1), str(p2)) ]

@router.delete("/pins/connect", status_code=200)
def disconnect_pin(
    session: DBSession, # type: ignore
    pdp: BoardPDP,
    board_id: UUID,
    p1: UUID,
    p2: UUID,
) -> list[Pin]:
    """Deletes a connection between two pins on this board."""
    return [ convert_pin(pin) for pin in items_db.remove_pin_connection(session, pdp, str(board_id), str(p1), str(p2)) ]

@router.post("/pins", status_code=201)
def create_pin(
    session: DBSession, # type: ignore
    pdp: BoardPDP,
    board_id: UUID,
    config: PinCreate,
) -> Pin:
    """Creates a pin on this board."""
    return convert_pin( items_db.create_pin(session, pdp, str(board_id), config) )

@router.put("/pins/{pin_id}", status_code=200)
def update_pin(
    session: DBSession, # type: ignore
    pdp: BoardPDP,
    board_id: UUID,
    pin_id: UUID,
    config: PinUpdate,
) -> Pin:
    """Updates a pin on this board."""
    return convert_pin( items_db.update_pin(session, pdp, str(board_id), str(pin_id), config) )

@router.delete("/pins/{pin_id}", status_code=204)
def delete_pin(
    session: DBSession, # type: ignore
    pdp: BoardPDP,
    board_id: UUID,
    pin_id: UUID,
):
    """Deletes a pin on this board."""
    items_db.delete_pin(session, pdp, str(board_id), str(pin_id))