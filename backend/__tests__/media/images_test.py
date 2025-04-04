"""Module to test routes related to uploading image"""

from backend.config import settings
from PIL import Image
import uuid
import os
from io import BytesIO

def test_upload_image(client, monkeypatch, auth_headers, create_image, static_path):
    id, filename = 'test_upload_image', 'test_upload_image.png'
    # override elements for verification
    monkeypatch.setattr(uuid, 'uuid4', lambda: id)
    monkeypatch.setattr(settings, 'static_path', static_path)
    # create an image
    image: Image = create_image(600, 400)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    # try to upload
    response = client.post(
        "/media/images/upload",
        headers=auth_headers(1),
        files={
            "file": (filename, buffer, 'image/png')
        }
    )
    # assert response
    assert response.json() == {
        'uuid': id,
        'filename': filename
    }
    assert response.status_code == 201
    # assert that the image was created correctly
    image = Image.open(os.path.join(static_path, 'images', filename))
    assert image.getpixel((0,0)) == (255, 255, 255)
    assert image.getpixel((599,0)) == (255, 255, 255)
    assert image.getpixel((0,399)) == (255, 255, 255)
    assert image.getpixel((599,399)) == (255, 255, 255)