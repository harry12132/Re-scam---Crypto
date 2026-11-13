from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage


def send_visit_alert(campaign: dict, visited_at: str) -> None:
    host = os.getenv("RESCAM_SMTP_HOST")
    sender = os.getenv("RESCAM_ALERT_FROM")
    recipient = os.getenv("RESCAM_ALERT_TO")
    if not all((host, sender, recipient)):
        return

    port = int(os.getenv("RESCAM_SMTP_PORT", "587"))
    username = os.getenv("RESCAM_SMTP_USERNAME")
    password = os.getenv("RESCAM_SMTP_PASSWORD")

    message = EmailMessage()
    message["Subject"] = f"Re-scam: campaign page opened ({campaign['id']})"
    message["From"] = sender
    message["To"] = recipient
    message.set_content(
        "A Re-scam simulation page was opened.\n\n"
        f"Campaign: {campaign['id']}\n"
        f"Opened at: {visited_at}\n"
        "No visitor identity or device information was collected."
    )

    with smtplib.SMTP(host, port, timeout=15) as smtp:
        smtp.starttls()
        if username and password:
            smtp.login(username, password)
        smtp.send_message(message)
