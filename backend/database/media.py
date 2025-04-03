from sqlalchemy import select

from fastapi import UploadFile

from backend.dependencies import DBSession
from backend.database.schema import DBUser, DBImage
from backend.exceptions import *

from backend.config import settings

from PIL import Image
from io import BytesIO
import uuid
import os

async def upload_file(session: DBSession, user: DBUser, file: UploadFile, content_length: int) -> DBImage:
    """Route to upload a file"""
    # Make sure it's the right size
    if content_length > settings.media_img_max_bytes:
        raise FileTooLarge('image', '1 MB')
    # Make sure the file type is supported
    if file.content_type not in [ "image/jpg", "image/png" ]:
        raise UnsupportedFileType(file.content_type, 'image')
    # Read the file and be absolutely sure the length is small enough (in case they mess up the content length header)
    contents = await file.read()
    if len(contents) > settings.media_img_max_bytes:
        raise FileTooLarge('image', '1 MB')
    # Convert to a PIL image
    image = Image.open(BytesIO(contents))
    # Resize to no larger than 600x600
    largest_dim = max(image.size)
    if largest_dim > 600:
        aspect_ratio = float(image.size[0]) / float(image.size[1])
        # if aspect ratio >= 1, then x is the largest dimension and is over 600px
        if aspect_ratio >= 1:
            image = image.resize(( 600, int(600 / aspect_ratio) ))
        else:
            image = image.resize(( int(600 * aspect_ratio), 600 ))
    # Figure out the extension
    ext: str = {
        'image/jpg': 'jpg',
        'image/png': 'png',
    }[file.content_type]
    # Generate a UUID 
    id = str(uuid.uuid4())
    filename = f"{id}.{ext}"
    # Save the image to the database
    db_image = DBImage(
        uuid=id,
        uploader_id=user.id,
        filename='/'.join(['static', 'images', filename]),
    )
    session.add(db_image)
    session.commit()
    session.refresh(db_image)
    # Save to static directory (after trying to insert, on the one in a quintillion chance that we get a collision)
    filepath = os.path.join(settings.static_path, 'images', filename)
    image.save(filepath)
    # return
    return db_image