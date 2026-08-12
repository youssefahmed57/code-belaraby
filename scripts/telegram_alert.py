import logging
import os
import sys

import httpx


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

HEALTH_ENDPOINT = os.getenv(
    "STAGING_HEALTH_URL",
    "https://code-belaraby-backend-staging.onrender.com/api/v1/health/detailed",
)
HEALTH_MONITOR_TOKEN = os.getenv("HEALTH_MONITOR_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram_alert(message: str) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("Telegram credentials are not configured; writing alert locally instead.")
        logging.error(message)
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": f"🚨 [تنبيه منصة كود بالعربي]\n\n{message}",
        "parse_mode": "HTML",
    }
    try:
        response = httpx.post(url, json=payload, timeout=5.0)
        if response.status_code == 200:
            logging.info("Telegram alert sent successfully.")
        else:
            logging.error("Failed to send Telegram alert: HTTP %s", response.status_code)
    except Exception as exc:
        logging.error("Exception sending Telegram alert: %s", exc)


def check_system_health() -> int:
    logging.info("Checking health status at: %s", HEALTH_ENDPOINT)
    headers = {}
    if HEALTH_MONITOR_TOKEN:
        headers["X-Health-Monitor-Token"] = HEALTH_MONITOR_TOKEN

    try:
        response = httpx.get(HEALTH_ENDPOINT, timeout=5.0, headers=headers)
    except Exception as exc:
        send_telegram_alert(f"🚨 تعذر الاتصال بخادم المنصة!\nالخطأ: <code>{str(exc)}</code>")
        return 1

    if response.status_code != 200:
        send_telegram_alert(f"⚠️ الخادم أعاد استجابة غير صحيحة!\nHTTP Status: {response.status_code}")
        return 1

    data = response.json()
    checks = data.get("checks") or {}
    overall_status = data.get("status")
    database_status = checks.get("database")
    redis_status = checks.get("redis")
    storage_status = checks.get("storage")

    critical_failure = (
        overall_status != "healthy"
        or database_status != "connected"
        or redis_status != "connected"
    )
    if critical_failure:
        send_telegram_alert(
            "<b>⚠️ انخفاض في أداء النظام أو انقطاع إحدى الخدمات!</b>\n\n"
            f"• الحالة العامة: <b>{overall_status}</b>\n"
            f"• قاعدة البيانات (DB): <code>{database_status}</code>\n"
            f"• الذاكرة المؤقتة (Redis): <code>{redis_status}</code>\n"
            f"• التخزين (Storage): <code>{storage_status}</code>"
        )
        return 1

    logging.info("All services healthy (DB, Redis, Storage).")
    return 0


if __name__ == "__main__":
    sys.exit(check_system_health())
