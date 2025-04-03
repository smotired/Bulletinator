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

async def upload_image(session: DBSession, user: DBUser, file: UploadFile, content_length: int, mindim: int = 0, maxdim: int = 600) -> DBImage:
    """Route to upload a file. Resizes it to the specified dimensions."""
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
    # Resize the image to below the max size, and then scale it back up if it's below the min size. this will need lots of testing
    original_image = image.copy()
    largest_dim = max(image.size)
    aspect_ratio = float(image.size[0]) / float(image.size[1])
    if largest_dim > maxdim:
        # if aspect ratio >= 1, then x is the largest dimension and is over max_px
        if aspect_ratio >= 1:
            image = original_image.resize(( maxdim, int(maxdim / aspect_ratio) ))
        else:
            image = original_image.resize(( int(maxdim * aspect_ratio), maxdim ))
    smallest_dim = min(image.size)
    if smallest_dim < mindim:
        # if aspect ratio >= 1, then y is the smallest dimension and is under min_px
        if aspect_ratio >= 1:
            image = original_image.resize(( int(mindim * aspect_ratio), mindim ))
        else:
            image = original_image.resize(( mindim, int(mindim / aspect_ratio) ))
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
        filename=filename,
    )
    session.add(db_image)
    session.commit()
    session.refresh(db_image)
    # Save to static directory (after trying to insert, on the one in a quintillion chance that we get a collision)
    filepath = os.path.join(settings.static_path, 'images', filename)
    image.save(filepath)
    # return
    return db_image

def delete_image(session: DBSession, image_uuid: str, user: DBUser) -> None:
    """Deletes an image in the database and from the static directory, if the user is the uploader."""
    # Get the image and verify that this user uploaded it
    image: DBImage = session.get(DBImage, image_uuid)
    if image == None:
        raise EntityNotFound('image', 'uuid', image_uuid)
    if image.uploader != user:
        raise AccessDenied()
    # Delete file
    filepath = os.path.join(settings.static_path, 'images', image.filename)
    try:
        os.remove(filepath)
    except OSError:
        pass
    # Delete from database
    session.delete(image)
    session.commit()

async def upload_avatar(session: DBSession, user: DBUser, image: UploadFile, content_length: int) -> DBUser:
    """Uploads an image, resizes it to 64x64, sets the user's profile picture to that image, and returns the user."""
    # Upload the image and resize to 64x64
    image: DBImage = await upload_image(session, user, image, content_length, mindim=64, maxdim=64)
    # Update the user
    user.profile_image = image.filename
    session.add(user)
    session.commit()
    session.refresh(user)
    return user