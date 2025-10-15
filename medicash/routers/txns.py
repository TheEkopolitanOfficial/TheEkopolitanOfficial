from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional, Literal
from ..store import store
from ..models import Transaction, Dispute, MerchantToken
from .auth import require_auth
from datetime import datetime, timedelta

router = APIRouter(prefix="/txns", tags=["transactions"])


@router.post("/simulate-preauth")
def simulate_preauth(
    card_id: str,
    amount: float,
    currency: str = "USD",
    merchant_name: str = "Merchant",
    mcc: str = "5999",
    merchant_id: Optional[str] = None,
    country: str = "US",
    presentment_mode: Literal["online", "card_present"] = "online",
    user_id: str = Depends(require_auth),
):
    card = store.cards.get(card_id)
    if not card or card.user_id != user_id:
        raise HTTPException(status_code=404, detail="Card not found")
    if card.status != "active":
        raise HTTPException(status_code=403, detail="Card not active")
    # Controls enforcement
    if presentment_mode not in card.presentment_modes:
        raise HTTPException(status_code=403, detail="Presentment mode blocked")
    if card.merchant_whitelist is not None and merchant_id not in (card.merchant_whitelist or []):
        raise HTTPException(status_code=403, detail="Merchant not whitelisted")
    if card.mcc_allow is not None and mcc not in (card.mcc_allow or []):
        raise HTTPException(status_code=403, detail="MCC blocked")
    if card.geo_allow_countries is not None and country not in (card.geo_allow_countries or []):
        raise HTTPException(status_code=403, detail="Country blocked")
    # Spend limit enforcement
    if card.spend_limit_amount and card.spend_limit_interval:
        now = datetime.utcnow()
        if card.spend_limit_interval == "daily":
            window_start = now - timedelta(days=1)
        elif card.spend_limit_interval == "weekly":
            window_start = now - timedelta(weeks=1)
        elif card.spend_limit_interval == "monthly":
            window_start = now - timedelta(days=30)
        else:
            window_start = now - timedelta(days=30)
        spent = 0.0
        for t in store.txns.values():
            if t.user_id == user_id and t.card_id == card_id and t.created_at >= window_start and t.status == "posted" and t.type == "capture":
                spent += abs(t.posted_amount or t.amount)
        if spent + amount > card.spend_limit_amount:
            raise HTTPException(status_code=402, detail="Spend limit exceeded")
    txn = Transaction(
        user_id=user_id,
        card_id=card_id,
        merchant_name=merchant_name,
        merchant_id=merchant_id,
        mcc=mcc,
        currency=currency,
        amount=amount,
        type="preauth",
        status="pending",
        auth_hold_amount=amount,
        metadata={"country": country, "presentment_mode": presentment_mode},
    )
    store.add_txn(txn)
    # Simulate storing merchant token on first auth
    if merchant_id:
        exists = any(
            (tok.card_id == card_id and tok.user_id == user_id and tok.merchant_id == merchant_id)
            for tok in store.tokens.values()
        )
        if not exists:
            mt = MerchantToken(user_id=user_id, merchant_id=merchant_id, merchant_name=merchant_name, card_id=card_id)
            store.tokens[mt.id] = mt
    return txn


@router.post("/{txn_id}/post")
def post_capture(txn_id: str, amount: Optional[float] = None, user_id: str = Depends(require_auth)):
    txn = store.txns.get(txn_id)
    if not txn or txn.user_id != user_id:
        raise HTTPException(status_code=404, detail="Txn not found")
    txn.type = "capture"
    txn.status = "posted"
    txn.posted_amount = amount or txn.auth_hold_amount or txn.amount
    # Auto-close single-use cards after first capture
    card = store.cards.get(txn.card_id)
    if card and card.type == "single_use" and card.status == "active":
        card.status = "closed"
    return txn


@router.post("/{txn_id}/refund")
def refund(txn_id: str, amount: float, user_id: str = Depends(require_auth)):
    base = store.txns.get(txn_id)
    if not base or base.user_id != user_id:
        raise HTTPException(status_code=404, detail="Txn not found")
    refund_txn = Transaction(
        user_id=user_id,
        card_id=base.card_id,
        merchant_name=base.merchant_name,
        mcc=base.mcc,
        currency=base.currency,
        amount=-abs(amount),
        type="refund",
        status="posted",
    )
    store.add_txn(refund_txn)
    return refund_txn


@router.post("/{txn_id}/dispute")
def create_dispute(txn_id: str, reason: str, amount: float, user_id: str = Depends(require_auth)):
    base = store.txns.get(txn_id)
    if not base or base.user_id != user_id:
        raise HTTPException(status_code=404, detail="Txn not found")
    dispute = Dispute(txn_id=txn_id, user_id=user_id, reason=reason, amount=amount)
    store.disputes[dispute.id] = dispute
    return dispute


@router.post("/{dispute_id}/evidence")
async def upload_evidence(dispute_id: str, file: UploadFile = File(...), user_id: str = Depends(require_auth)):
    dispute = store.disputes.get(dispute_id)
    if not dispute or dispute.user_id != user_id:
        raise HTTPException(status_code=404, detail="Dispute not found")
    # For demo, we won't save file, just record a pseudo URL
    pseudo_url = f"evidence://{dispute_id}/{file.filename}"
    dispute.evidence_urls.append(pseudo_url)
    return {"status": "uploaded", "url": pseudo_url}


@router.post("/{txn_id}/receipt")
async def upload_receipt(txn_id: str, file: UploadFile = File(...), user_id: str = Depends(require_auth)):
    txn = store.txns.get(txn_id)
    if not txn or txn.user_id != user_id:
        raise HTTPException(status_code=404, detail="Txn not found")
    pseudo_url = f"receipt://{txn_id}/{file.filename}"
    txn.receipts_urls.append(pseudo_url)
    return {"status": "uploaded", "url": pseudo_url}


@router.post("/{dispute_id}/submit")
def submit_dispute(dispute_id: str, user_id: str = Depends(require_auth)):
    d = store.disputes.get(dispute_id)
    if not d or d.user_id != user_id:
        raise HTTPException(status_code=404, detail="Dispute not found")
    d.status = "submitted"
    return d


@router.post("/{dispute_id}/resolve")
def resolve_dispute(
    dispute_id: str,
    result: Literal["resolved", "partial_credit", "rejected"] = "resolved",
    credit_amount: Optional[float] = None,
    user_id: str = Depends(require_auth),
):
    d = store.disputes.get(dispute_id)
    if not d or d.user_id != user_id:
        raise HTTPException(status_code=404, detail="Dispute not found")
    if result == "partial_credit" and (credit_amount is None or credit_amount <= 0):
        raise HTTPException(status_code=400, detail="Credit amount required for partial credit")
    d.status = result
    if result in ("resolved", "partial_credit") and credit_amount:
        base = store.txns.get(d.txn_id)
        if base:
            refund_txn = Transaction(
                user_id=user_id,
                card_id=base.card_id,
                merchant_name=base.merchant_name,
                mcc=base.mcc,
                currency=base.currency,
                amount=-abs(credit_amount),
                type="refund",
                status="posted",
                metadata={"dispute_id": dispute_id},
            )
            store.add_txn(refund_txn)
    return d
