from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Literal
from ..store import store
from ..models import Card, Transaction, Dispute, MerchantToken, ShareLink
from .auth import require_auth
from datetime import datetime, timedelta
import random

router = APIRouter(prefix="/cards", tags=["cards"])


class CreateCard(BaseModel):
    label: str
    type: Literal["physical", "virtual", "single_use"] = "virtual"


class UpdateControls(BaseModel):
    mcc_allow: Optional[List[str]] = None
    merchant_whitelist: Optional[List[str]] = None
    geo_allow_countries: Optional[List[str]] = None
    presentment_modes: Optional[List[Literal["card_present", "online"]]] = None
    spend_limit_amount: Optional[float] = None
    spend_limit_interval: Optional[Literal["daily", "weekly", "monthly", "rolling_30d"]] = None
    magstripe_enabled: Optional[bool] = None
    contactless_offline_limit: Optional[float] = None


@router.post("/create")
def create_card(payload: CreateCard, user_id: str = Depends(require_auth)):
    card = Card(user_id=user_id, label=payload.label, type=payload.type)
    store.add_card(card)
    return card


@router.get("")
def list_cards(user_id: str = Depends(require_auth)):
    return store.list_user_cards(user_id)


@router.post("/{card_id}/freeze")
def freeze_card(card_id: str, user_id: str = Depends(require_auth)):
    card = store.cards.get(card_id)
    if not card or card.user_id != user_id:
        raise HTTPException(status_code=404, detail="Card not found")
    card.status = "frozen"
    return card


@router.post("/{card_id}/unfreeze")
def unfreeze_card(card_id: str, user_id: str = Depends(require_auth)):
    card = store.cards.get(card_id)
    if not card or card.user_id != user_id:
        raise HTTPException(status_code=404, detail="Card not found")
    card.status = "active"
    return card


@router.post("/{card_id}/reissue")
def reissue_card(card_id: str, user_id: str = Depends(require_auth)):
    old = store.cards.get(card_id)
    if not old or old.user_id != user_id:
        raise HTTPException(status_code=404, detail="Card not found")
    old.status = "replaced"
    new_card = Card(user_id=user_id, label=f"{old.label} (reissue)", type=old.type)
    old.replaced_by_card_id = new_card.id
    store.add_card(new_card)
    return {"old": old, "new": new_card}


@router.post("/{card_id}/controls")
def update_controls(card_id: str, payload: UpdateControls, user_id: str = Depends(require_auth)):
    card = store.cards.get(card_id)
    if not card or card.user_id != user_id:
        raise HTTPException(status_code=404, detail="Card not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(card, field, value)
    return card


@router.get("/{card_id}/tokens")
def list_merchant_tokens(card_id: str, user_id: str = Depends(require_auth)):
    card = store.cards.get(card_id)
    if not card or card.user_id != user_id:
        raise HTTPException(status_code=404, detail="Card not found")
    return [t for t in store.tokens.values() if t.card_id == card_id and t.user_id == user_id]


class RevokeToken(BaseModel):
    token_id: str


@router.post("/{card_id}/tokens/revoke")
def revoke_token(card_id: str, payload: RevokeToken, user_id: str = Depends(require_auth)):
    token = store.tokens.get(payload.token_id)
    if not token or token.user_id != user_id or token.card_id != card_id:
        raise HTTPException(status_code=404, detail="Token not found")
    del store.tokens[payload.token_id]
    return {"status": "revoked"}


@router.post("/{card_id}/share-link")
def create_share_link(card_id: str, user_id: str = Depends(require_auth)):
    card = store.cards.get(card_id)
    if not card or card.user_id != user_id:
        raise HTTPException(status_code=404, detail="Card not found")
    masked_pan = "4111 11XX XXXX 1111"
    link = ShareLink(
        user_id=user_id,
        card_id=card_id,
        expires_at=datetime.utcnow() + timedelta(minutes=10),
        masked_pan=masked_pan,
        cvc_hint="**3",
    )
    store.shares[link.id] = link
    return {"share_id": link.id, "url": f"/cards/share/{link.id}"}


@router.get("/share/{share_id}")
def get_share_link(share_id: str, user_id: str = Depends(require_auth)):
    link = store.shares.get(share_id)
    if not link or link.user_id != user_id:
        raise HTTPException(status_code=404, detail="Share not found")
    if link.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Share expired")
    return link


class PinResetRequest(BaseModel):
    code: str


@router.post("/{card_id}/pin-reset")
def pin_reset(card_id: str, payload: PinResetRequest, user_id: str = Depends(require_auth)):
    card = store.cards.get(card_id)
    if not card or card.user_id != user_id:
        raise HTTPException(status_code=404, detail="Card not found")
    if payload.code != "123456":
        raise HTTPException(status_code=400, detail="Invalid verification code")
    return {"pin_reset": True}


@router.post("/{card_id}/rotate-credentials")
def rotate_credentials(card_id: str, user_id: str = Depends(require_auth)):
    card = store.cards.get(card_id)
    if not card or card.user_id != user_id:
        raise HTTPException(status_code=404, detail="Card not found")
    last4 = random.randint(1000, 9999)
    masked_pan = f"4111 11XX XXXX {last4}"
    cvc_hint = f"**{random.randint(0,9)}"
    return {"masked_pan": masked_pan, "cvc_hint": cvc_hint}
