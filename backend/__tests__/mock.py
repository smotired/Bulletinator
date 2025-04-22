"""Mock methods for tests"""

from uuid import UUID
from backend.database.schema import DBAccount, DBEmailVerification

# Password verification
def hash_password(p: str) -> str:
    return "hashed_" + p
def check_password(p: str, h: str) -> bool:
    return "hashed_" + p == h

# UUID
def to_uuid(i: int, entity: str = None) -> str:
    i = i + (OFFSETS[entity] if entity else 0)
    return str(UUID(f"{i:08}-{i:04}-{i:04}-{i:04}-{i:012}"))

last_uuid = 0
def uuid() -> str:
    global last_uuid
    last_uuid += 1
    return to_uuid(last_uuid)

def black_hole():
    """Black hole function to make sure some functions just don't even get called, such as sending emails."""

# UUID offsets for tests.
# Used to make tests a little more resistant to adding test data.
OFFSETS = {
    'account': 0,
    'board': 1000,
    'item': 2000,
    'sub_item': 3000,
    'pin': 4000,
    'media': 5000,
    'report': 6000,
    'permission': 500
}

# Essentially turn off rate limits
KEY_LIMITS = {
    "forced": (100, 1),
    "main": (100, 1),
    "auth": (100, 1),
    "account": (100, 1),
    "from_email": (100, 1),
    "board": (100, 1),
    "board_action": (100, 1),
    "submit_report": (100, 1),
    "media": (100, 1),
    "static": (100, 1),
}