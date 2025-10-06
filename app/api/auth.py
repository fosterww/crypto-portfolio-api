from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import EmailStr
from app.db.session import get_db
from app.db.models import User
from app.schemas.auth import SignUpIn, Token
from app.schemas.user import UserOut
from app.utils.hash import hash_password, verify_password
from app.core.security import create_token

router = APIRouter()

@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def signup(payload: SignUpIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    u = User(email=str(payload.email), password_hash=hash_password(payload.password))
    db.add(u); db.commit(); db.refresh(u)
    return u

@router.post("/login", response_model=Token)
def login(email: EmailStr, password: str, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.email == email).first()
    if not u or not verify_password(password, u.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_token({"sub": str(u.id)})
    return Token(access_token=token)