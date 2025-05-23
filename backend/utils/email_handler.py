"""Handles everything related to sending emails for various reasons."""

from os import path

from backend.config import settings
from backend.database.schema import DBAccount, DBCustomer, DBBoard, DBEmailVerification, DBPasswordChangeRequest, DBEditorInvitation

import smtplib
from email.message import EmailMessage
from email.headerregistry import Address
from email.utils import make_msgid

# Type of text replacements for the dictionary
TextReplacements = dict[str, dict[str, str]]

def send_verification_email(account: DBAccount, verification: DBEmailVerification):
    name = account.display_name or account.username
    message: EmailMessage = compose_email(
        "verification",
        "Verify your Bulletinator account",
        Address(name, addr_spec=verification.email),
        {
            "[VID]": verification.id,
            "[NAME]": name,
        }
    )
    send_email(message)

def send_password_change_email(account: DBAccount, request: DBPasswordChangeRequest):
    name = account.display_name or account.username
    message: EmailMessage = compose_email(
        "password_change",
        "Reset your Bulletinator password",
        Address(name, addr_spec=account.email),
        {
            "[PID]": request.id,
            "[NAME]": name,
        }
    )
    send_email(message)

def send_update_verification_email(account: DBAccount, verification: DBEmailVerification):
    name = account.display_name or account.username
    message: EmailMessage = compose_email(
        "update_verification",
        "Verify your new email address",
        Address(name, addr_spec=verification.email),
        {
            "[VID]": verification.id,
            "[NAME]": name,
        }
    )
    send_email(message)

def send_editor_invitation_email(board: DBBoard, invitation: DBEditorInvitation, editor_email: str):
    message: EmailMessage = compose_email(
        "invitation",
        "You've been invited to a Bulletin Board!",
        Address(editor_email, addr_spec=editor_email),
        {
            "[IID]": invitation.id,
            "[BOARD]": board.name,
            "[BLINK_TXT]": "" if not board.public else f"\n\nhttps://www.bulletinator.com/boards/{board.id}",
            "[BLINK_HTML]": board.name if not board.public else f"<a href=\"https://www.bulletinator.com/boards/{board.id}\">{board.name}</a>",
        }
    )
    send_email(message)

def send_purchase_confirmation_email(customer: DBCustomer):
    name = customer.account.display_name or customer.account.username
    message: EmailMessage = compose_email(
        "subscription",
        "Welcome to Bulletinator Premium.",
        Address(name, addr_spec=customer.account.email),
        {
            "[NAME]": name,
        }
    )
    send_email(message)

def send_subscription_failure_email(customer: DBCustomer):
    name = customer.account.display_name or customer.account.username
    message: EmailMessage = compose_email(
        "subscription_failure",
        "Bulletinator: Subscription renewal failure.",
        Address(name, addr_spec=customer.account.email),
        {
            "[NAME]": name,
        }
    )
    send_email(message)

def send_subscription_cancellation_email(customer: DBCustomer):
    name = customer.account.display_name or customer.account.username
    message: EmailMessage = compose_email(
        "subscription_cancellation",
        "Sorry to see you go!",
        Address(name, addr_spec=customer.account.email),
        {
            "[NAME]": name,
        }
    )
    send_email(message)

def send_email(message: EmailMessage):
    with smtplib.SMTP_SSL(
        host=settings.smtp_host,
        port=settings.smtp_port,
    ) as server:
        server.login(settings.smtp_login, settings.smtp_password)
        server.send_message( message )

def compose_email(type: str, subject: str, to_address: Address, replacements: TextReplacements) -> EmailMessage:
    """Method to compose an email with certain text replacements and a certain address. Assumes HTML file has an img element with src='cid:[HEADERCID]'.
    
    Args:
        type (str): The type of message, corresponding to files in the assets/emails folder
        subject (str): The message subject
        to_addr (Address): The address of the recipient user
        replacements (TextReplacements): Replacements for the body of the plaintext and html files

    returns:
        EmailMessage: The constructed message
    """
    # Extract from content files
    with open(path.join(settings.assets_folder_path, 'header.png'), 'rb') as img:
        header_img_cid = make_msgid()
        header_img = img.read()
    with open(path.join(settings.assets_folder_path, 'emails', f'{type}.txt'), 'r') as txt:
        plain_text = txt.read()
        for key in replacements:
            plain_text = plain_text.replace(key, replacements[key])
    with open(path.join(settings.assets_folder_path, 'emails', f'{type}.html'), 'r') as html:
        html_alt = html.read().replace("[HEADERCID]", header_img_cid[1:-1]) # peels off the <> around the CID
        for key in replacements:
            html_alt = html_alt.replace(key, replacements[key])

    # Set up the headers
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = Address("Bulletinator", addr_spec=settings.smtp_sender)
    message["To"] = to_address

    # Add text and html content
    message.set_content(plain_text)
    message.add_alternative(html_alt, subtype='html')

    # Add header image
    message.get_payload()[1].add_related(header_img, 'image', 'png', cid=header_img_cid)

    # Make a local copy before returning
    with open(path.join(settings.assets_folder_path, 'emails', f'{type}.msg'), 'wb') as f:
        f.write(bytes(message))

    return message