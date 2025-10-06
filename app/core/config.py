from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseModel):
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    JWT_SECRET: str = os.getenv("JWT_SECRET")
    JWT_ALG: str = os.getenv("JWT_ALG", "HS256")
    REDIS_URL: str = os.getenv("REDIS_URL")

settings = Settings()