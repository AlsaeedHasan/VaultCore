from os import getenv
from typing import List

from dotenv import load_dotenv
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME=getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=getenv("MAIL_PASSWORD"),
    MAIL_FROM=getenv("MAIL_FROM"),
    MAIL_PORT=getenv("MAIL_PORT"),
    MAIL_SERVER=getenv("MAIL_SERVER", 587),
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
