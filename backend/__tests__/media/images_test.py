"""Module to test routes related to uploading image"""

from backend.config import settings
from PIL import Image
import uuid
import os
from io import BytesIO

def test_upload_image(client, monkeypatch, auth_headers, create_image, static_path):
    id = 'test_upload_image'
    filename = id + '.png'
    # override elements for verification
    monkeypatch.setattr(uuid, 'uuid4', lambda: id)
    monkeypatch.setattr(settings, 'static_path', static_path)
    # delete the image if it exists
    try:
        os.remove(os.path.join(static_path, 'images', filename))
    except OSError:
        pass
    # create an image
    image: Image = create_image(600, 600)
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
    assert image.getpixel((0,599)) == (255, 255, 255)
    assert image.getpixel((599,599)) == (255, 255, 255)

def test_upload_image_unauthenticated(client, monkeypatch, create_image, static_path, exception):
    id = 'test_upload_image_unauthenticated'
    filename = id + '.png'
    # override elements for verification
    monkeypatch.setattr(uuid, 'uuid4', lambda: id)
    monkeypatch.setattr(settings, 'static_path', static_path)
    # delete the image if it exists
    try:
        os.remove(os.path.join(static_path, 'images', filename))
    except OSError:
        pass
    # create an image
    image: Image = create_image(100, 100)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    # try to upload
    response = client.post(
        "/media/images/upload",
        files={
            "file": (filename, buffer, 'image/png')
        }
    )
    # assert response
    assert response.json() == exception('not_authenticated', 'Not authenticated')
    assert response.status_code == 403

def test_upload_toobig_image(client, monkeypatch, auth_headers, create_image, static_path, exception):
    id = 'test_upload_toobig_image'
    filename = id + '.png'
    # override elements for verification
    monkeypatch.setattr(uuid, 'uuid4', lambda: id)
    monkeypatch.setattr(settings, 'static_path', static_path)
    # delete the image if it exists
    try:
        os.remove(os.path.join(static_path, 'images', filename))
    except OSError:
        pass
    # create an image
    image: Image = create_image(800, 800, True)
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
    assert response.json() == exception('file_too_large', "Files of type 'image' must be no larger than 1 MB")
    assert response.status_code == 422

def test_upload_image_oversize(client, monkeypatch, auth_headers, create_image, static_path):
    id = 'test_upload_image_oversize'
    filename = id + '.png'
    # override elements for verification
    monkeypatch.setattr(uuid, 'uuid4', lambda: id)
    monkeypatch.setattr(settings, 'static_path', static_path)
    # delete the image if it exists
    try:
        os.remove(os.path.join(static_path, 'images', filename))
    except OSError:
        pass
    # create an image
    image: Image = create_image(900, 900)
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
    assert image.getpixel((0,599)) == (255, 255, 255)
    assert image.getpixel((599,599)) == (255, 255, 255)

def test_upload_image_oversize_x(client, monkeypatch, auth_headers, create_image, static_path):
    id = 'test_upload_image_oversize_x'
    filename = id + '.png'
    # override elements for verification
    monkeypatch.setattr(uuid, 'uuid4', lambda: id)
    monkeypatch.setattr(settings, 'static_path', static_path)
    # delete the image if it exists
    try:
        os.remove(os.path.join(static_path, 'images', filename))
    except OSError:
        pass
    # create an image
    image: Image = create_image(900, 600)
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

def test_upload_image_oversize_y(client, monkeypatch, auth_headers, create_image, static_path):
    id = 'test_upload_image_oversize_y'
    filename = id + '.png'
    # override elements for verification
    monkeypatch.setattr(uuid, 'uuid4', lambda: id)
    monkeypatch.setattr(settings, 'static_path', static_path)
    # delete the image if it exists
    try:
        os.remove(os.path.join(static_path, 'images', filename))
    except OSError:
        pass
    # create an image
    image: Image = create_image(600, 900)
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
    assert image.getpixel((399,0)) == (255, 255, 255)
    assert image.getpixel((0,599)) == (255, 255, 255)
    assert image.getpixel((399,599)) == (255, 255, 255)

def test_upload_avatar(client, monkeypatch, auth_headers, create_image, static_path, get_user):
    id = 'test_upload_avatar'
    filename = id + '.png'
    # override elements for verification
    monkeypatch.setattr(uuid, 'uuid4', lambda: id)
    monkeypatch.setattr(settings, 'static_path', static_path)
    # delete the image if it exists
    try:
        os.remove(os.path.join(static_path, 'images', filename))
    except OSError:
        pass
    # create an image
    image: Image = create_image(64, 64)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    # try to upload
    response = client.post(
        "/media/avatar/upload",
        headers=auth_headers(1),
        files={
            "file": (filename, buffer, 'image/png')
        }
    )
    # assert response
    expected = get_user(1).copy()
    expected['profile_image'] = filename
    assert response.json() == expected
    assert response.status_code == 201
    # assert that the image was created correctly
    image = Image.open(os.path.join(static_path, 'images', filename))
    assert image.getpixel((0,0)) == (255, 255, 255)
    assert image.getpixel((63,0)) == (255, 255, 255)
    assert image.getpixel((0,63)) == (255, 255, 255)
    assert image.getpixel((63,63)) == (255, 255, 255)

def test_upload_avatar_oversize(client, monkeypatch, auth_headers, create_image, static_path, get_user):
    id = 'test_upload_avatar_oversize'
    filename = id + '.png'
    # override elements for verification
    monkeypatch.setattr(uuid, 'uuid4', lambda: id)
    monkeypatch.setattr(settings, 'static_path', static_path)
    # delete the image if it exists
    try:
        os.remove(os.path.join(static_path, 'images', filename))
    except OSError:
        pass
    # create an image
    image: Image = create_image(96, 96)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    # try to upload
    response = client.post(
        "/media/avatar/upload",
        headers=auth_headers(1),
        files={
            "file": (filename, buffer, 'image/png')
        }
    )
    # assert response
    expected = get_user(1).copy()
    expected['profile_image'] = filename
    assert response.json() == expected
    assert response.status_code == 201
    # assert that the image was created correctly
    image = Image.open(os.path.join(static_path, 'images', filename))
    assert image.getpixel((0,0)) == (255, 255, 255)
    assert image.getpixel((63,0)) == (255, 255, 255)
    assert image.getpixel((0,63)) == (255, 255, 255)
    assert image.getpixel((63,63)) == (255, 255, 255)

def test_upload_avatar_oversize_x(client, monkeypatch, auth_headers, create_image, static_path, get_user):
    id = 'test_upload_avatar_oversize_x'
    filename = id + '.png'
    # override elements for verification
    monkeypatch.setattr(uuid, 'uuid4', lambda: id)
    monkeypatch.setattr(settings, 'static_path', static_path)
    # delete the image if it exists
    try:
        os.remove(os.path.join(static_path, 'images', filename))
    except OSError:
        pass
    # create an image
    image: Image = create_image(96, 64)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    # try to upload
    response = client.post(
        "/media/avatar/upload",
        headers=auth_headers(1),
        files={
            "file": (filename, buffer, 'image/png')
        }
    )
    # assert response
    expected = get_user(1).copy()
    expected['profile_image'] = filename
    assert response.json() == expected
    assert response.status_code == 201
    # assert that the image was created correctly
    image = Image.open(os.path.join(static_path, 'images', filename))
    assert image.getpixel((0,0)) == (255, 255, 255)
    assert image.getpixel((95,0)) == (255, 255, 255)
    assert image.getpixel((0,63)) == (255, 255, 255)
    assert image.getpixel((95,63)) == (255, 255, 255)

def test_upload_avatar_oversize_y(client, monkeypatch, auth_headers, create_image, static_path, get_user):
    id = 'test_upload_avatar_oversize_y'
    filename = id + '.png'
    # override elements for verification
    monkeypatch.setattr(uuid, 'uuid4', lambda: id)
    monkeypatch.setattr(settings, 'static_path', static_path)
    # delete the image if it exists
    try:
        os.remove(os.path.join(static_path, 'images', filename))
    except OSError:
        pass
    # create an image
    image: Image = create_image(64, 96)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    # try to upload
    response = client.post(
        "/media/avatar/upload",
        headers=auth_headers(1),
        files={
            "file": (filename, buffer, 'image/png')
        }
    )
    # assert response
    expected = get_user(1).copy()
    expected['profile_image'] = filename
    assert response.json() == expected
    assert response.status_code == 201
    # assert that the image was created correctly
    image = Image.open(os.path.join(static_path, 'images', filename))
    assert image.getpixel((0,0)) == (255, 255, 255)
    assert image.getpixel((63,0)) == (255, 255, 255)
    assert image.getpixel((0,95)) == (255, 255, 255)
    assert image.getpixel((63,95)) == (255, 255, 255)

def test_upload_image_jpg(client, monkeypatch, auth_headers, create_image, static_path):
    id = 'test_upload_image_jpg'
    filename = id + '.jpg'
    # override elements for verification
    monkeypatch.setattr(uuid, 'uuid4', lambda: id)
    monkeypatch.setattr(settings, 'static_path', static_path)
    # delete the image if it exists
    try:
        os.remove(os.path.join(static_path, 'images', filename))
    except OSError:
        pass
    # create an image
    image: Image = create_image(200, 200)
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)
    # try to upload
    response = client.post(
        "/media/images/upload",
        headers=auth_headers(1),
        files={
            "file": (filename, buffer, 'image/jpg')
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
    assert image.getpixel((0,0)) == (245, 245, 245) # jpeg compression is weird but consistent
    assert image.getpixel((199,0)) == (245, 245, 245)
    assert image.getpixel((0,199)) == (245, 245, 245)
    assert image.getpixel((199,199)) == (245, 245, 245)