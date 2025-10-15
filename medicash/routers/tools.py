from fastapi import APIRouter, Depends
from ..store import store
from .auth import require_auth
from pydantic import BaseModel
from typing import List
import shortuuid

router = APIRouter(prefix="/tools", tags=["tools"])


class ATMEstimateRequest(BaseModel):
    country: str
    amount: float


@router.post("/atm-estimate")
def atm_estimate(payload: ATMEstimateRequest, user_id: str = Depends(require_auth)):
    # Mocked estimator: fee 2% + fixed 2, and limit 400 per withdrawal
    fee = round(payload.amount * 0.02 + 2, 2)
    limit = 400
    return {"fee": fee, "suggested_withdrawals": int((payload.amount + limit - 1) // limit)}


class CoverageRequest(BaseModel):
    country: str


@router.post("/coverage")
def acceptance_coverage(payload: CoverageRequest, user_id: str = Depends(require_auth)):
    # Mocked coverage
    coverage = {
        "contactless": 0.85,
        "chip_pin": 0.95,
        "magstripe": 0.40,
        "atm": 0.75,
        "transit_open_loop": 0.60,
    }
    issues = [
        {"network": "Visa", "region": payload.country, "status": "degraded", "notes": "Intermittent 3DS timeouts"}
    ]
    return {"country": payload.country, "coverage": coverage, "known_issues": issues}


@router.post("/emergency-cash")
def emergency_cash(user_id: str = Depends(require_auth)):
    code = f"EC-{shortuuid.uuid()[:8].upper()}"
    return {"voucher_code": code, "amount_limit": 200, "expires_minutes": 60}
