from random import random
from datetime import datetime, UTC

from sqlalchemy import select
from sqlalchemy.orm import selectin_polymorphic, selectinload

from backend.dependencies import DBSession, format_list
from backend.database import boards as boards_db
from backend.database.schema import DBItem, DBBoard, DBAccount, DBItemNote, DBItemLink, DBItemMedia, DBItemTodo, DBItemList, DBPin
from backend.exceptions import *

from backend.models.items import *

# options for select
polymorphic = selectin_polymorphic(DBItem, [DBItemNote, DBItemLink, DBItemMedia, DBItemTodo, DBItemList])
loadlistcontents = selectinload(DBItemList.contents).options(polymorphic)

def get_by_id(session: DBSession, item_id: str, typestr: str = 'item') -> DBItem: # type: ignore
    """Returns the item with this ID"""
    # tragically due to polymorphism session.get doesn't work
    stmt = select(DBItem).options(polymorphic, loadlistcontents).where(DBItem.id == item_id)
    results = list(session.execute(stmt).scalars().all())
    if len(results) == 0:
        raise EntityNotFound(typestr, "id", item_id)
    return results[0]

def get_items(session: DBSession, board_id: str, account: DBAccount | None) -> list[DBItem]: # type: ignore
    """Returns the items on the board with this ID, if the account can see them"""
    board: DBBoard = boards_db.get_for_viewer(session, board_id, account)
    # Get a list of top-level items
    stmt = select(DBItem).options(polymorphic, loadlistcontents).where(DBItem.board_id == board_id).where(DBItem.list_id == None)
    items = list(session.execute(stmt).scalars().all())
    return items

def get_item(session: DBSession, board_id: str, item_id: str, account: DBAccount | None) -> DBItem: # type: ignore
    """Returns the item with this ID, if it's on the board with this ID and the account can see it."""
    board: DBBoard = boards_db.get_for_viewer(session, board_id, account)
    item = get_by_id(session, item_id)
    if item.board != board:
        raise EntityNotFound("item", "id", item_id)
    return item

def create_item(session: DBSession, board_id: str, config: ItemCreate, account: DBAccount | None) -> DBItem: # type: ignore
    """Creates an item on this board."""
    board: DBBoard = boards_db.get_for_editor(session, board_id, account)
    # Figure out what type of config this is
    subclass: type = ITEMTYPES.get(config.type, { "create": BaseItemCreate })['create']
    if subclass == BaseItemCreate:
        raise InvalidItemType(config.type)
    # Make sure it has the required fields
    config_dict = config.model_dump()
    required_fields: list[str] = ITEMTYPES.get(config.type)['required_fields'] # does not include Item's required fields, as those are required in BaseItemUpdate
    missing = [ f for f in required_fields if config_dict[f] == None ]
    if len(missing) > 0:
        raise MissingItemFields(config.type, format_list(missing))
    # Verify subclass fields
    if 'text' in config_dict and config_dict['text'] is not None and config.type in [ 'note', 'document' ]:
        if len(config_dict['text']) > { 'note': 300, 'document': 65536 }[ config.type ]:
            raise FieldTooLong('text')
    if 'size' in config_dict and config_dict['size'] is not None and config.type in [ 'note', 'media' ]:
        try:
            x, y, = config_dict['size'].split(',')
            xi, yi = int(x), int(y)
            if x != str(xi) or y != str(yi):
                raise InvalidField(config_dict['size'], 'size')
        except:
            raise InvalidField(config_dict['size'], 'size')
    if 'title' in config_dict and config_dict['title'] is not None and config.type in [ 'link', 'todo', 'list', 'document' ]:
        if len(config_dict['title']) > { 'link': 64, 'todo': 64, 'list': 64, 'document': 64 }[ config.type ]:
            raise FieldTooLong('title')
    if 'url' in config_dict and config_dict['url'] is not None and config.type in [ 'link', 'media' ]:
        if len(config_dict['url']) > { 'link': 128, 'media': 128 }[ config.type ]:
            raise FieldTooLong('url')
    # If a list_id is provided, try to get the list from the database and make some space
    if config_dict['list_id'] is not None:
        # make sure we aren't adding a list to a list
        if config.type == 'list':
            raise AddListToList()
        other: DBItemList = get_by_id(session, config_dict['list_id'], 'item_list')
        # make sure the list is also on this board
        if other.board_id != board_id:
            raise EntityNotFound('item_list', 'id', config_dict['list_id'])
        # make sure the other item is a list
        if other.type != "list":
            raise ItemTypeMismatch(other.id, 'list', other.type)
        # try to make space
        target = config_dict['index'] or len(other.contents)
        other = shift_list(session, other, target) # THIS MODIFIES THE DATABASE! IF MORE ERROR HANDLING IS ADDED TO THIS METHOD, IT MUST BE BEFORE THIS LINE!
        config_dict['index'] = target
    # Create a minimal dictionary
    dbclass: type = ITEMTYPES.get(config.type)['db']
    stripped_dict = dict( (k, v) for k, v in config_dict.items() if k in ITEMFIELDS or v is not None ) # remove fields for different subclasses
    stripped_dict['board_id'] = board_id
    # Create a DBItem for the subclass and add it to the database
    item: DBItem = dbclass(**stripped_dict)
    # Make sure to override position and index based on list status
    if item.list_id is not None:
        item.position = None
    else:
        item.index = None
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

def update_item(session: DBSession, board_id: str, item_id: str, config: ItemUpdate, account: DBAccount) -> DBItem: # type: ignore
    """Updates an item."""
    # Make sure the account can edit this board, and the item exists and is on this board.
    board: DBBoard = boards_db.get_for_editor(session, board_id, account)
    item: DBItem = get_by_id(session, item_id)
    if item.board_id != board_id:
        raise EntityNotFound('item', 'id', item_id)
    # Update subclass-specific item fields
    if config.text is not None and item.type in [ 'note', 'document' ]:
        if len(config.text) > { 'note': 300, 'document': 65536 }[ item.type ]:
            raise FieldTooLong('text')
        item.text = config.text
    if config.size is not None and item.type in [ 'note', 'media' ]:
        try:
            x, y, = config.size.split(',')
            xi, yi = int(x), int(y)
            if x != str(xi) or y != str(yi):
                raise InvalidField(config.size, 'size')
        except:
            raise InvalidField(config.size, 'size')
        item.size = config.size
    if config.title is not None and item.type in [ 'link', 'todo', 'list', 'document' ]:
        if len(config.title) > { 'link': 64, 'todo': 64, 'list': 64, 'document': 64 }[ item.type ]:
            raise FieldTooLong('title')
        item.title = config.title
    if config.url is not None and item.type in [ 'link', 'media' ]:
        if len(config.url) > { 'link': 128, 'media': 128  }[ item.type ]:
            raise FieldTooLong('url')
        item.url = config.url
    # Only universal fields that can be updated are position, link and index.
    lists_to_collapse: list[DBItemList] = [] # lists that had things removed or swapped around and should be collapsed after items are updated
    # If a position is provided, remove from any list.
    if config.position is not None:
        if item.list:
            lists_to_collapse.append(item.list)
        item.list_id = None
        item.index = None
        item.position = config.position
    # ELSE, if a list_id is provided that doesn't match the current list_id, remove from the current list and add to that list.
    elif config.list_id is not None and config.list_id != item.list_id:
        # make sure we aren't adding a list to a list
        if item.type == 'list':
            raise AddListToList()
        # make sure we actually can add to the other list, if not, leave as-is
        other: DBItemList = get_by_id(session, config.list_id, 'item_list')
        # make sure the list is also on this board
        if other.board_id != board_id:
            raise EntityNotFound('item_list', 'id', config.list_id)
        # make sure the other item is a list
        if other.type != "list":
            raise ItemTypeMismatch(other.id, 'list', other.type)
        # try to make space
        target = config.index if config.index is not None else len(other.contents)
        other = shift_list(session, other, target) # THIS MODIFIES THE DATABASE! IF MORE ERROR HANDLING IS ADDED TO THIS METHOD, IT MUST BE BEFORE THIS LINE!
        config.index = target
        # prepare to move
        if item.list:
            lists_to_collapse.append(item.list)
        item.list_id = config.list_id
        item.index = config.index
        item.position = None
    # ELSE, if index is provided, update position in current list (list_id either isn't provided or is the same so that's fine. unless this isn't in a list in which case should throw indexoutofrange)
    elif config.index is not None:
        if item.list_id is None:
            raise IndexOutOfRange('item', item_id, config.index)
        # make space and prepare to move
        lists_to_collapse.append(item.list)
        item.list = shift_list(session, item.list, config.index)
        item.index = config.index
    # OTHERWISE nothing about the item's location was provided, so leave that alone.
    # Update in database.
    item.updated_at = datetime.now(UTC)
    session.add(item)
    session.commit()
    session.refresh(item)
    # Collapse lists before returning
    for l in lists_to_collapse:
        collapse_list(session, l)
    return item

def delete_item(session: DBSession, board_id: str, item_id: str, account: DBAccount) -> None: # type: ignore
    """Delets an item."""
    # Make sure the account can edit this board, and the item exists and is on this board.
    board: DBBoard = boards_db.get_for_editor(session, board_id, account)
    item: DBItem = get_by_id(session, item_id)
    if item.board_id != board_id:
        raise EntityNotFound('item', 'id', item_id)
    # Deleting a list deletes all child objects with ondelete=cascade
    # Delete and collapse any containing list
    item_list: DBItemList | None = item.list
    session.delete(item)
    session.commit()
    if item_list:
        collapse_list(session, item_list)

def create_todo_item(session: DBSession, board_id: str, config: TodoItemCreate, account: DBAccount) -> DBTodoItem: # type: ignore
    """Creates and returns a TodoItem in this todo list"""
    board: DBBoard = boards_db.get_for_editor(session, board_id, account)
    todo: DBItemTodo = get_by_id(session, config.list_id, 'item_todo')
    if todo.board_id != board_id:
        raise EntityNotFound('item_todo', 'id', config.list_id)
    if todo.type != 'todo':
        raise ItemTypeMismatch(todo.id, 'todo', todo.type)
    if len(config.text) > 128:
        raise FieldTooLong('text')
    if config.link is not None and len(config.link) > 128:
        raise FieldTooLong('link')
    todo_item = DBTodoItem(
        list_id = config.list_id,
        text=config.text,
        link=config.link,
        done=config.done
    )
    todo.updated_at = datetime.now(UTC)
    session.add(todo)
    session.add(todo_item)
    session.commit()
    session.refresh(todo_item)
    return todo_item

def update_todo_item(session: DBSession, board_id: str, todo_item_id: str, config: TodoItemUpdate, account: DBAccount) -> DBTodoItem: # type: ignore
    """Creates and returns a TodoItem in this todo list"""
    board: DBBoard = boards_db.get_for_editor(session, board_id, account)
    todo_item = session.get(DBTodoItem, todo_item_id)
    if todo_item == None:
        raise EntityNotFound('todo_item', 'id', todo_item_id)
    todo: DBItemTodo = get_by_id(session, todo_item.list_id, 'item_todo')
    if todo.board_id != board_id:
        raise EntityNotFound(f'todo_item', 'id', todo_item_id)
    if todo.type != 'todo':
        raise ItemTypeMismatch(todo.id, 'todo', todo.type)
    # update fields
    todo.updated_at = datetime.now(UTC)
    session.add(todo)
    if config.text is not None:
        if len(config.text) > 128:
            raise FieldTooLong('text')
        todo_item.text = config.text
    if config.link is not None:
        if len(config.link) > 128:
            raise FieldTooLong('link')
        todo_item.link = config.link
    if config.done is not None:
        todo_item.done = config.done
    session.add(todo_item)
    session.commit()
    session.refresh(todo_item)
    return todo_item

def delete_todo_item(session: DBSession, board_id: str, todo_item_id: str, account: DBAccount) -> None: # type: ignore
    """Deletes a todo item"""
    board: DBBoard = boards_db.get_for_editor(session, board_id, account)
    todo_item = session.get(DBTodoItem, todo_item_id)
    if todo_item == None:
        raise EntityNotFound('todo_item', 'id', todo_item_id)
    todo: DBItemTodo = get_by_id(session, todo_item.list_id, 'item_todo')
    if todo.board_id != board_id:
        raise EntityNotFound('todo_item', 'id', todo_item_id)
    if todo.type != 'todo':
        raise ItemTypeMismatch(todo.id, 'todo', todo.type)
    session.delete(todo_item)
    session.commit()

def shift_list(session: DBSession, list: DBItemList, start_index: int) -> DBItemList: # type: ignore
    """Shifts the items on this list after this index by one, leaving an open space, and then return the list. Used for when you want to add something at this new index."""
    if start_index < 0 or start_index > len(list.contents):
        raise IndexOutOfRange("item_list", list.id, start_index)
    sorted_contents = sorted(list.contents, key=lambda item: item.index)
    # update all the item indices
    for i, item in enumerate(sorted_contents):
        if i >= start_index:
            item.index = i + 1
            session.add(item)
    list.updated_at = datetime.now(UTC)
    session.add(list)
    session.commit()
    session.refresh(list)
    return list

def collapse_list(session: DBSession, list: DBItemList) -> DBItemList: # type: ignore
    """Refreshes a list's indices. Replaces them so they start at 0 and go up by 1."""
    sorted_contents = sorted(list.contents, key=lambda item: item.index)
    # update all the item indices
    for i, item in enumerate(sorted_contents):
        item.index = i
        session.add(item)
    list.updated_at = datetime.now(UTC)
    session.add(list)
    session.commit()
    session.refresh(list)
    return list

def create_pin(session: DBSession, board_id: str, config: PinCreate, account: DBAccount) -> DBPin: # type: ignore
    """Adds a pin to an item."""
    board: DBBoard = boards_db.get_for_editor(session, board_id, account)
    item: DBItem = get_by_id(session, config.item_id)
    if item.board_id != board_id:
        raise EntityNotFound('item', 'id', config.item_id)
    if item.pin is not None:
        raise DuplicateEntity('pin', 'item_id', config.item_id)
    if config.label is not None and len(config.label) > 64:
        raise FieldTooLong('label')
    pin = DBPin(
        board_id=board_id,
        item_id=config.item_id,
        label=config.label,
        compass=config.compass,
    )
    item.updated_at = datetime.now(UTC) 
    session.add(item)
    session.add(pin)
    session.commit()
    session.refresh(pin)
    return pin

def update_pin(session: DBSession, board_id: str, pin_id: str, config: PinUpdate, account: DBAccount) -> DBPin: # type: ignore
    """Updates a pin."""
    board: DBBoard = boards_db.get_for_editor(session, board_id, account)
    pin: DBPin = session.get(DBPin, pin_id)
    if pin == None:
        raise EntityNotFound('pin', 'id', pin_id)
    if config.item_id is not None:
        item: DBItem = get_by_id(session, config.item_id)
        if item.board_id != board_id:
            raise EntityNotFound('item', 'id', config.item_id)
        if item.pin is not None:
            raise DuplicateEntity('pin', 'item_id', config.item_id)
        pin.item_id = config.item_id
    if config.label is not None:
        if len(config.label) > 64:
            raise FieldTooLong('label')
        pin.label = config.label
    if config.compass is not None:
        pin.compass = config.compass
    session.add(pin)
    session.commit()
    session.refresh(pin)
    return pin

def delete_pin(session: DBSession, board_id: str, pin_id: str, account: DBAccount) -> None: # type: ignore
    """Deletes a pin."""
    board: DBBoard = boards_db.get_for_editor(session, board_id, account)
    pin: DBPin = session.get(DBPin, pin_id)
    if pin == None:
        raise EntityNotFound('pin', 'id', pin_id)
    pin.item.updated_at = datetime.now(UTC) 
    session.add(pin.item)
    session.delete(pin)
    session.commit()

def add_pin_connection(session: DBSession, board_id: str, pin1_id: str, pin2_id: str, account: DBAccount) -> list[DBPin]: # type: ignore
    """Adds a connection between two pins."""
    board: DBBoard = boards_db.get_for_editor(session, board_id, account)
    pin1: DBPin = session.get(DBPin, pin1_id)
    if pin1 == None or pin1.board_id != board_id:
        raise EntityNotFound('pin', 'id', pin1_id)
    pin2: DBPin = session.get(DBPin, pin2_id)
    if pin2 == None or pin2.board_id != board_id:
        raise EntityNotFound('pin', 'id', pin2_id)
    pin1.connections.append(pin2)
    pin2.connections.append(pin1)
    session.add(pin1)
    session.add(pin2)
    session.commit()
    session.refresh(pin1)
    session.refresh(pin2)
    return [ pin1, pin2 ]

def remove_pin_connection(session: DBSession, board_id: str, pin1_id: str, pin2_id: str, account: DBAccount) -> list[DBPin]: # type: ignore
    """Removes a connection between two pins."""
    board: DBBoard = boards_db.get_for_editor(session, board_id, account)
    pin1: DBPin = session.get(DBPin, pin1_id)
    if pin1 == None or pin1.board_id != board_id:
        raise EntityNotFound('pin', 'id', pin1_id)
    pin2: DBPin = session.get(DBPin, pin2_id)
    if pin2 == None or pin2.board_id != board_id:
        raise EntityNotFound('pin', 'id', pin2_id)
    if pin2 in pin1.connections:
        pin1.connections.remove(pin2)
    if pin1 in pin2.connections:
        pin2.connections.remove(pin1)
    session.add(pin1)
    session.add(pin2)
    session.commit()
    session.refresh(pin1)
    session.refresh(pin2)
    return [ pin1, pin2 ]
