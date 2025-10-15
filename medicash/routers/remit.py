from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ..store import store
from ..models import RemittanceQuote, RemittanceTransfer
from .auth import require_auth

router = APIRouter(prefix="/remit", tags=["remittance"])


class QuoteRequest(BaseModel):
    send_currency: str
    receive_currency: str
    send_amount: float


@router.post("/quote")
def quote(payload: QuoteRequest, user_id: str = Depends(require_auth)):
    # Mock FX rate and fee
    rate = 0.9 if payload.send_currency == "USD" and payload.receive_currency == "EUR" else 1.0
    fee = 2.5
    receive_amount = round(payload.send_amount * rate - fee, 2)
    q = RemittanceQuote(user_id=user_id, receive_amount=receive_amount, rate=rate, fee=fee, **payload.model_dump())
    store.quotes[q.id] = q
    return q


class TransferRequest(BaseModel):
    quote_id: str
    beneficiary_name: str
    beneficiary_iban: str | None = None
    beneficiary_mobile: str | None = None


@router.post("/transfer")
def transfer(payload: TransferRequest, user_id: str = Depends(require_auth)):
    q = store.quotes.get(payload.quote_id)
    t = RemittanceTransfer(user_id=user_id, quote_id=payload.quote_id, beneficiary_name=payload.beneficiary_name, beneficiary_iban=payload.beneficiary_iban, beneficiary_mobile=payload.beneficiary_mobile)
    store.transfers[t.id] = t
    t.status = "settled"
    return t
