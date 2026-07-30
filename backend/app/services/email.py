"""Отправка почты — по решению заказчика пока не подключена реальным
провайдером (нет готового SMTP на момент внедрения модуля доступа). Если
SMTP_HOST не задан, письмо не отправляется: вызывающий код (forgot-password)
обязан в этом случае сам предусмотреть admin-видимый fallback, а не считать,
что письмо ушло.
"""
import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger("app.email")


def is_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_FROM_EMAIL)


def send_email(to: str, subject: str, body: str) -> bool:
    """Возвращает True, если письмо реально отправлено. False (без
    исключения) означает «SMTP не настроен» — вызывающий код должен
    обработать это как обычный, ожидаемый случай, а не как ошибку."""
    if not is_configured():
        logger.info("SMTP не настроен, письмо для %s не отправлено: %s", to, subject)
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = to
    message.set_content(body)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_USE_TLS:
            server.starttls()
        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(message)
    return True
