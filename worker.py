import asyncio
from typing import List
from celery import Celery
import os
from utils import send_email
from fastapi_mail import errors
from dotenv import load_dotenv

load_dotenv()

BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
BACKEND_URL = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")


celery_app = Celery("vaultcore", broker=BROKER_URL, backend=BACKEND_URL)


@celery_app.task(
    name="send_email",
    autoretry_for=(
        errors.ApiError,
        errors.ConnectionErrors,
    ),
    retry_backoff=True,
    max_retries=5,
)
def start_sending_email(
    subject: str,
    recipients: List[str],
    url: str,
    template="verification_mail.html",
):
    with open(f"mail_templates/{template}", "r") as template:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            
            asyncio.set_event_loop(asyncio.new_event_loop())
        asyncio.run(
            send_email(
                subject=subject,
                recipients=recipients,
                body=template.read().replace("{verification_url}", url),
            )
        )
    return {"msg": "email sent"}
