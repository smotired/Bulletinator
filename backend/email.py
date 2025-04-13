"""Handles everything related to sending emails for various reasons."""

from backend.config import settings
from backend.database.schema import DBAccount, DBEmailVerification
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_verification_email(account: DBAccount, verification: DBEmailVerification):
    with smtplib.SMTP_SSL(
        host=settings.smtp_host,
        port=settings.smtp_port,
    ) as server:
        server.login(settings.smtp_login, settings.smtp_password)
        server.sendmail(
            settings.smtp_sender,
            verification.email,
            compose_verification_email(account, verification)
        )

def compose_verification_email(account: DBAccount, verification: DBEmailVerification):
    # Specify HTML 
    # TODO: load this from a file god damn
    html = """\
<html>
  <style>
    body {
      margin: 0;
      padding: 0;
      background: #eeeeee;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
    }

    main {
      display: block;
      width: 60%;
      margin: 1rem auto;
      background: #ffffff;
      box-shadow: 5px 5px 10px #888888;
      border-radius: 2px;
    }

    main section{
      padding: 2rem;
    }

    h1 {
      text-align: center;
    }

    p.button {
      text-align: center;
      margin-top: 2rem;
    }

    p.button a {
      background-color: #262262;
      background-size: 100% 200%;
      background-position: 0 100%;
      background-image: radial-gradient(circle at 72% -71%, #2bb673 26%, transparent 68.05%);
      color: white;
      border-radius: 0.5rem;
      padding: 1rem 2rem;
      text-decoration: none;
      transition: all 0.1s ease-in-out;
      box-shadow: 0px 0px 0px #888888;
    }

    p.button a:hover {
      text-decoration: underline;
      background-color: #264482;
      background-position: 0% 0%;
      box-shadow: 2px 2px 8px #888888;
    }

    p.sm {
      color: #888888;
      text-align: center;
      font-size: 0.75rem;
    }

    @media(max-width: 50rem) {
      main {
        width: calc(100% - 1rem - 3rem);
      }
    }
  </style>
  <body>
    <main>
      <section>
        <h1>Welcome, {account.display_name or account.username}!</h1>
        <p>Thanks for creating a Bulletinator account. Verify your email to start managing projects.</p>
        <p class="button"><a class="button" href="https://www.bulletinator.com/verify-email/{verification.id}" target="_blank" rel="noopener noreferrer">Verify Email</a></p>
      </section>
    </main>
    <p class="sm">Questions? Shoot an email to <a href="mailto:support@bulletinator.com">support@bulletinator.com</a>.</p>
  </body>
</html>
"""

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = settings.smtp_sender
    message["To"] = settings.smtp_sender
    message["Subject"] = "Verify your Bulletinator account"

    # Attach the HTML part
    message.attach(MIMEText(html, "html"))

    return message.as_string()