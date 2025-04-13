"""Handles everything related to sending emails for various reasons."""

from backend.config import settings
from backend.database.schema import DBAccount, DBEmailVerification
import smtplib

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
    return f"""
From: Bulletinator <{settings.smtp_sender}>
To: {account.display_name or account.username} <{verification.email}>
Subject: Verify your Bulletinator account


Hello {account.display_name or account.username},

Thank you for signing up for bulletinator.

Please click the link below to verify your email.

https://www.bulletinator.com/verify_email/{verification.id}

This link will expire after 24 hours.

Welcome to Bulletinator!
"""[1:-1] # trim off start and end newlines