from fastapi import HTTPException
from fastapi_mail import ConnectionConfig
from decouple import config
import logging

conf = ConnectionConfig(
    MAIL_USERNAME=config("MAIL_USERNAME"),
    MAIL_PASSWORD=config("MAIL_PASSWORD"),
    MAIL_FROM=config("MAIL_FROM"),
    MAIL_PORT=config("MAIL_PORT"),
    MAIL_SERVER=config("MAIL_SERVER"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=False
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_email(subject: str, email_to: str, body: str):
    try:
        logger.info("\n=== Email Simulation ===")
        logger.info(f"Subject: {subject}")
        logger.info(f"To: {email_to}")
        logger.info(f"Body:\n{body}")
        logger.info("========================\n")
    except Exception as e:
        logger.error(f"Failed to send email to {email_to}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send email")
