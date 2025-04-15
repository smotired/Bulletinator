"""Handles everything related to sending emails for various reasons."""

from backend.config import settings
from backend.database.schema import DBAccount, DBEmailVerification
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

def send_verification_email(account: DBAccount, verification: DBEmailVerification):
    with smtplib.SMTP_SSL(
        host=settings.smtp_host,
        port=settings.smtp_port,
    ) as server:
        server.login(settings.smtp_login, settings.smtp_password)
        server.send_message( compose_verification_email(account, verification) )

def compose_verification_email(account: DBAccount, verification: DBEmailVerification) -> MIMEMultipart:
    # Specify plain text
    text = f"""\
Welcome, {account.display_name or account.username}!

Thanks for creating a Bulletinator account. Verify your email by clicking the link below to start managing projects.
https://www.bulletinator.com/verify-email/{verification.id}

You received this email because this email address was used to register an account at Bulletinator.com.
If you did not intend create an account, you can safely ignore this email.
"""

    # Specify HTML 
    html = f"""\
<html>
  <body style="margin: 0; padding: 1rem 0; background-color: #eeeeee; font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;">
    <div style="width: calc(100% - 3rem); max-width: 40rem; margin: auto; background-color: #ffffff; padding: 2rem 1.5rem;">
      <img src="https://i.imgur.com/iR9I0NN.png" alt="Bulletinator Logo" style="display: block; margin: auto; max-height:5rem; max-width: 80%;" />
        <h1 style="text-align: center;">Welcome, {account.display_name or account.username}!</h1>
        <p style="text-align: center;">Thanks for creating a Bulletinator account. Verify your email to start managing projects.</p>
        <p style="text-align: center; margin-top: 2rem;">
          <a href="https://www.bulletinator.com/verify-email/{verification.id}" target="_blank" rel="noopener noreferrer" style="background-color: #262262; color: white; text-decoration: none; border-radius: 0.5rem; padding: 1rem 2rem;">
            Verify Email
          </a>
        </p>
    </div>
    <p style="color: #888888; margin: 1rem; text-align: center; font-size: 0.75rem;">
      You received this email because this email address was used to register an account at <a href="https://www.bulletinator.com/" target="_blank" rel="noopener noreferrer">Bulletinator.com</a>.
    </p>
    <p style="color: #888888; margin: 1rem; text-align: center; font-size: 0.75rem;">
      If you did not intend create an account, you can safely ignore this email.
    </p>
  </body>
</html>
""" # TODO: Replace image link once frontend is hosted

    # Create a multipart message and set headers
    message = MIMEMultipart("alternative")
    message["From"] = formataddr(("Bulletinator", settings.smtp_sender))
    message["To"] = formataddr((account.display_name or account.username, verification.email))
    message["Subject"] = "Verify your Bulletinator account"

    # Attach different segments
    message.attach(MIMEText(text, "plain"))
    message.attach(MIMEText(html, "html"))

    return message