from __future__ import annotations
from typing import Optional
import pyotp
from .config import settings


def generate_otp_secret(email: str) -> str:
    # For demo, deterministic secret from email; replace with DB per-user secret
    return pyotp.random_base32()


def verify_otp(email: str, code: str, secret: Optional[str] = None) -> bool:
    secret = secret or generate_otp_secret(email)
    totp = pyotp.TOTP(secret, issuer=settings.otp_issuer)
    return totp.verify(code, valid_window=1)
