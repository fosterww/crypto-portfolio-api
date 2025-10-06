import time, jwt
from typing import Any, Optional
from app.core.config import settings

def create_token(sub: Any, exp_sec: int = 60*80*24) -> str:
    now = int(time.time())
    payload = {"sub": str(sub), "exp": now + exp_sec, "iat": now}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])

def get_user_id_from_token(token: str) -> Optional[str]:
    try:
        payload = decode_token(token)
        return int(payload.get("sub"))
    except Exception:
        return None