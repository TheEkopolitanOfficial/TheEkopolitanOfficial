from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..store import store

router = APIRouter(prefix="/auth", tags=["auth"])


class RequestOTP(BaseModel):
    email: str


class VerifyOTP(BaseModel):
    email: str
    code: str


@router.post("/request-otp")
def request_otp(payload: RequestOTP):
    # In a real app, send email. Here, return code for demo simplicity.
    user = store.get_or_create_user(payload.email)
    # Demo code is always 123456 for ease of use in this prototype
    return {"message": "OTP sent", "demo_code": "123456", "user_id": user.id}


@router.post("/verify-otp")
def verify_otp(payload: VerifyOTP):
    if payload.code != "123456":
        raise HTTPException(status_code=400, detail="Invalid code")
    user = store.get_or_create_user(payload.email)
    session = store.create_session(user.id)
    return {"token": session.token, "user_id": user.id}


def require_auth(authorization: Optional[str] = Header(None)) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = authorization.replace("Bearer ", "")
    session = store.get_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return session.user_id
