"""Handles everything related to sending emails for various reasons."""

from os import path

from backend.config import settings
from backend.database.schema import DBAccount, DBEmailVerification

import smtplib
from email.message import EmailMessage
from email.headerregistry import Address
from email.utils import make_msgid

def send_verification_email(account: DBAccount, verification: DBEmailVerification):
    with smtplib.SMTP_SSL(
        host=settings.smtp_host,
        port=settings.smtp_port,
    ) as server:
        server.login(settings.smtp_login, settings.smtp_password)
        server.send_message( compose_verification_email(account, verification) )

def compose_verification_email(account: DBAccount, verification: DBEmailVerification) -> EmailMessage:
    # Extract from content files
    with open(path.join(settings.assets_folder_path, 'header.png'), 'rb') as img:
        header_img_cid = make_msgid()
        header_img = img.read()
    with open(path.join(settings.assets_folder_path, 'emails', 'verification.txt'), 'r') as txt:
        plain_text = txt.read().replace("[VID]", verification.id).replace("[NAME]", account.display_name or account.username)
    with open(path.join(settings.assets_folder_path, 'emails', 'verification.html'), 'r') as html:
        html_alt = html.read().replace("[VID]", verification.id).replace("[NAME]", account.display_name or account.username).replace("[HEADERCID]", header_img_cid[1:-1]) # peels off the <> around the CID

    # Set up the headers
    message = EmailMessage()
    message["Subject"] = "Verify your Bulletinator account"
    message["From"] = Address("Bulletinator", addr_spec=settings.smtp_sender)
    message["To"] = Address(account.display_name or account.username, addr_spec=verification.email)

    # Add text and html content
    message.set_content(plain_text)
    message.add_alternative(html_alt, subtype='html')

    # Add header image
    message.get_payload()[1].add_related(header_img, 'image', 'png', cid=header_img_cid)

    # Make a local copy before returning
    with open(path.join(settings.assets_folder_path, 'emails', 'verification.msg'), 'wb') as f:
        f.write(bytes(message))

    return message