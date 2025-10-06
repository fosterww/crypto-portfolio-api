from pydantic import BaseModel, EmailStr

class SignUpIn(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"