from fastapi import HTTPException
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from decouple import config
import logging

conf = ConnectionConfig(
    MAIL_USERNAME=config("MAIL_USERNAME"),
    MAIL_PASSWORD=config("MAIL_PASSWORD"),
    MAIL_FROM=config("MAIL_FROM"),
    MAIL_PORT=config("MAIL_PORT", cast=int),
    MAIL_SERVER=config("MAIL_SERVER"),
    MAIL_FROM_NAME=config("MAIL_FROM_NAME"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_email(subject: str, email_to: str, body: str) -> None:
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=body,
        subtype=MessageType.html 
    )

    fm = FastMail(conf)

    try:
        await fm.send_message(message)
        logger.info(f"Email sent successfully to {email_to}")
    except ConnectionErrors as e:
        logger.error(f"Failed to send email to {email_to}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send email, please try again later.")
