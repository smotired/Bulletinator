"""Router for authentication routes.

Args:
    router (APIRouter): Router for /auth routes
"""

from fastapi import APIRouter, Response

from backend.database.schema import *
from backend.dependencies import DBSession

router = APIRouter(prefix="/auth", tags=["Authentication"])