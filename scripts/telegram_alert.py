import os
import sys
import httpx
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

HEALTH_ENDPOINT = os.getenv("STAGING_HEALTH_URL", "https://code-belaraby-backend-staging.onrender.com/api/v1/health/detailed")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_alert(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("Telegram Bot Token or Chat ID missing in environment. Printing alert locally:")
        logging.error(message)
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": f"🚨 [تنبيه منصة كود بالعربي]\n\n{message}",
        "parse_mode": "HTML"
    }
    try:
        r = httpx.post(url, json=payload, timeout=5.0)
        if r.status_code == 200:
            logging.info("Telegram alert sent successfully.")
        else:
            logging.error(f"Failed to send Telegram alert: HTTP {r.status_code}")
    except Exception as e:
        logging.error(f"Exception sending Telegram alert: {e}")

def check_system_health():
    logging.info(f"Checking health status at: {HEALTH_ENDPOINT}")
    try:
        r = httpx.get(HEALTH_ENDPOINT, timeout=5.0)
        if r.status_code != 200:
            send_telegram_alert(f"⚠️ الخادم يعيد استجابة غير صحيحة!\nHTTP Status: {r.status_code}")
            return

        data = r.json()
        overall_status = data.get("status")
        db_status = data.get("database")
        redis_status = data.get("redis")
        storage_status = data.get("storage")

        if overall_status != "healthy" or db_status != "connected" or redis_status != "connected":
            alert_msg = (
                f"<b>⚠️ انخفاض في أداء النظام أو انقطاع إحدى الخدمات!</b>\n\n"
                f"• الحالة العامة: <b>{overall_status}</b>\n"
                f"• قاعدة البيانات (DB): <code>{db_status}</code>\n"
                f"• الذاكرة المؤقتة (Redis): <code>{redis_status}</code>\n"
                f"• التخزين السحابي (Storage): <code>{storage_status}</code>"
            )
            send_telegram_alert(alert_msg)
        else:
            logging.info("All services healthy (DB, Redis, Storage).")
    except Exception as e:
        send_telegram_alert(f"🚨 تعذر الاتصال بخادم المنصة!\nالخطأ: <code>{str(e)}</code>")

if __name__ == "__main__":
    check_system_health()
