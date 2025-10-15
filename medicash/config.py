from pydantic import BaseModel
from typing import Optional
import os


class Settings(BaseModel):
    app_name: str = "MedICash"
    environment: str = os.getenv("ENV", "dev")
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key-change")
    access_token_exp_minutes: int = 60 * 24 * 14
    otp_issuer: str = "medicash.co"
    base_url: str = os.getenv("BASE_URL", "http://localhost:8000")


settings = Settings()