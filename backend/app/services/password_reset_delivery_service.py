import smtplib
from email.message import EmailMessage
from typing import Any

import httpx

from app.core.config import settings
from app.db.models import User


class PasswordResetDeliveryUnavailable(RuntimeError):
    pass


_mock_password_reset_deliveries: list[dict[str, Any]] = []


def clear_mock_password_reset_deliveries() -> None:
    _mock_password_reset_deliveries.clear()


def get_mock_password_reset_deliveries() -> list[dict[str, Any]]:
    return list(_mock_password_reset_deliveries)


class PasswordResetDeliveryService:
    @staticmethod
    def _build_reset_link(raw_token: str) -> str:
        return f"{settings.NEXT_PUBLIC_APP_URL.rstrip('/')}/reset-password?token={raw_token}"

    @staticmethod
    async def deliver_reset_token(user: User, raw_token: str) -> None:
        provider = settings.PASSWORD_RESET_DELIVERY_PROVIDER
        reset_link = PasswordResetDeliveryService._build_reset_link(raw_token)

        if provider == "mock":
            if not settings.is_development_like():
                raise PasswordResetDeliveryUnavailable(
                    "Password reset delivery is not configured for this environment."
                )
            _mock_password_reset_deliveries.append(
                {
                    "user_id": user.id,
                    "phone_number": user.phone_number,
                    "email": user.email,
                    "reset_link": reset_link,
                    "token": raw_token,
                }
            )
            return

        if provider == "disabled":
            raise PasswordResetDeliveryUnavailable(
                "Password reset delivery is disabled for this environment."
            )

        if provider == "smtp_email":
            if not settings.is_password_reset_delivery_configured():
                raise PasswordResetDeliveryUnavailable(
                    "SMTP password reset delivery is not fully configured."
                )
            if not user.email:
                raise PasswordResetDeliveryUnavailable("No email address is available for password reset delivery.")

            message = EmailMessage()
            message["Subject"] = "Password reset - Code Belaraby"
            message["From"] = settings.PASSWORD_RESET_SMTP_FROM
            message["To"] = user.email
            message.set_content(
                "Use the following secure link to reset your password:\n"
                f"{reset_link}\n\n"
                "If you did not request this change, you can ignore this message."
            )

            with smtplib.SMTP(settings.PASSWORD_RESET_SMTP_HOST, settings.PASSWORD_RESET_SMTP_PORT, timeout=10) as smtp:
                smtp.starttls()
                smtp.login(settings.PASSWORD_RESET_SMTP_USERNAME, settings.PASSWORD_RESET_SMTP_PASSWORD)
                smtp.send_message(message)
            return

        if provider == "sms_webhook":
            if not settings.is_password_reset_delivery_configured():
                raise PasswordResetDeliveryUnavailable(
                    "SMS password reset delivery is not fully configured."
                )
            if not user.phone_number:
                raise PasswordResetDeliveryUnavailable("No phone number is available for password reset delivery.")

            headers = {"Content-Type": "application/json"}
            if settings.PASSWORD_RESET_SMS_WEBHOOK_TOKEN:
                headers["Authorization"] = f"Bearer {settings.PASSWORD_RESET_SMS_WEBHOOK_TOKEN}"
            payload = {
                "phone_number": user.phone_number,
                "message": f"Code Belaraby password reset link: {reset_link}",
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(settings.PASSWORD_RESET_SMS_WEBHOOK_URL, json=payload, headers=headers)
            if response.status_code >= 400:
                raise PasswordResetDeliveryUnavailable("SMS password reset delivery provider rejected the request.")
            return

        raise PasswordResetDeliveryUnavailable("Unsupported password reset delivery provider.")
