import httpx, logging
import smtplib
from email.message import EmailMessage
from app.core.config import settings
from app.utils.http import with_retries

log = logging.getLogger(__name__)

async def send_telegram_global(text: str) -> bool:
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        log.info("[ALERT] %s", text); return False
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await with_retries(lambda: client.post(url, json={
                "chat_id": settings.TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"
            }))
            return resp.status_code == 200
        except Exception as e:
            log.warning("Telegram send failed: %s", e)
            return False
    
def send_email(to_email: str, subject: str, body: str) -> bool:
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["To"] = to_email
        msg["From"] = "noreply@example.com"
        msg.set_content(body)
        with smtplib.SMTP("localhost", 25) as s:
            s.send_message(msg)
        return True
    except Exception:
        return False