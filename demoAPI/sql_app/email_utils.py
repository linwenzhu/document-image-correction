from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr


conf = ConnectionConfig(
    MAIL_USERNAME="1904285808@qq.com",
    MAIL_PASSWORD="uwygthvbqdudciej",
    MAIL_FROM="1904285808@qq.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.qq.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)


async def send_email(email: EmailStr, subject: str, body: str):
    message = MessageSchema(
        subject=subject,
        recipients=[email],
        body=body,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)