from __future__ import annotations

import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass(frozen=True)
class EmailDeliveryResult:
    sent: bool
    logged_to_console: bool = False
    error: str | None = None


def send_email(*, to: str, subject: str, text_body: str, html_body: str | None = None) -> EmailDeliveryResult:
    """Send an email via SMTP when configured; otherwise log to console in development."""
    if settings.smtp_configured:
        try:
            _send_via_smtp(
                to=to,
                subject=subject,
                text_body=text_body,
                html_body=html_body,
            )
            return EmailDeliveryResult(sent=True)
        except Exception as exc:
            logger.exception("Failed to send email to %s", to)
            return EmailDeliveryResult(sent=False, error=str(exc))

    logger.info(
        "Email delivery skipped (SMTP not configured). To: %s | Subject: %s\n%s",
        to,
        subject,
        text_body,
    )
    return EmailDeliveryResult(sent=False, logged_to_console=True)


def _send_via_smtp(
    *,
    to: str,
    subject: str,
    text_body: str,
    html_body: str | None,
) -> None:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from
    message["To"] = to
    message.set_content(text_body)
    if html_body:
        message.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_user and settings.smtp_password:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(message)
