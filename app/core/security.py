import time, jwt
from typing import Any, Optional
from app.core.config import settings
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User

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
    

bearer = HTTPBearer(auto_error=False)

def get_current_user(
        creds = Depends(bearer),
        db: Session = Depends(get_db)
) -> User:
    token = creds.credentials if creds else None
    user_id = get_user_id_from_token(token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return u
    