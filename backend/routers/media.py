"""Router for boards routes.

Args:
    router (APIRouter): Router for /media routes
"""

from fastapi import APIRouter, UploadFile, Header
from fastapi.responses import FileResponse

from backend.database.schema import *
from backend.database import media as media_db
from backend.dependencies import DBSession, CurrentUser, OptionalUser
from backend.models.media import Image, ImageCollection
from backend.models.shared import Metadata

router = APIRouter(prefix="/media", tags=["Media"])

@router.post('/images/upload', status_code=201, response_model=Image)
async def upload_image_file(session: DBSession, user: CurrentUser, file: UploadFile, content_length: int = Header(None)) -> DBImage:
    """Route to upload an image file"""
    return await media_db.upload_file(session, user, file, content_length)

@router.delete('/images/{uuid}', status_code=204)
def delete_image(session: DBSession, user: CurrentUser, uuid: str):
    media_db.delete_image(session, uuid, user)