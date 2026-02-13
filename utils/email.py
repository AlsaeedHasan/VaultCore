from os import getenv
from typing import List

from dotenv import load_dotenv
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME=getenv("MAIL_USERNAME", "email@compancy.com"),
    MAIL_PASSWORD=getenv("MAIL_PASSWORD", "app_password"),
    MAIL_FROM=getenv("MAIL_FROM", "email@compancy.com"),
    MAIL_PORT=getenv("MAIL_PORT", 587),
    MAIL_SERVER=getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)


async def send_email(subject: str, recipients: List[EmailStr], body: str):
    msg = MessageSchema(
        subject=subject, body=body, recipients=recipients, subtype=MessageType.html
    )

    fm = FastMail(conf)

    await fm.send_message(msg)
