from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict
from datetime import datetime
import shortuuid


def generate_id(prefix: str) -> str:
    return f"{prefix}_{shortuuid.uuid()}"


class User(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("usr"))
    email: str
    is_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Session(BaseModel):
    token: str
    user_id: str
    expires_at: datetime


class Card(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("card"))
    user_id: str
    label: str
    status: Literal["active", "frozen", "replaced", "closed"] = "active"
    type: Literal["physical", "virtual", "single_use"] = "virtual"
    mcc_allow: Optional[List[str]] = None
    merchant_whitelist: Optional[List[str]] = None  # acquirer merchant IDs
    geo_allow_countries: Optional[List[str]] = None
    presentment_modes: List[Literal["card_present", "online"]] = ["online"]
    spend_limit_amount: Optional[float] = None
    spend_limit_interval: Optional[Literal["daily", "weekly", "monthly", "rolling_30d"]] = None
    magstripe_enabled: bool = False
    contactless_offline_limit: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    replaced_by_card_id: Optional[str] = None


class Transaction(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("txn"))
    user_id: str
    card_id: str
    merchant_name: str
    merchant_id: Optional[str] = None
    mcc: Optional[str] = None
    currency: str
    amount: float
    type: Literal["preauth", "capture", "refund", "reversal", "fee"] = "capture"
    status: Literal["pending", "posted", "reversed"] = "pending"
    auth_hold_amount: Optional[float] = None
    posted_amount: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, str] = {}
    receipts_urls: List[str] = []


class Dispute(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("dspt"))
    txn_id: str
    user_id: str
    reason: str
    amount: float
    evidence_urls: List[str] = []
    status: Literal["draft", "submitted", "resolved", "partial_credit", "rejected"] = "draft"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MerchantToken(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("tok"))
    user_id: str
    merchant_id: str
    merchant_name: str
    card_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TravelNotice(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("trvl"))
    user_id: str
    countries: List[str]
    start_date: datetime
    end_date: datetime


class ShareLink(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("share"))
    user_id: str
    card_id: str
    expires_at: datetime
    masked_pan: str
    cvc_hint: str


class RemittanceQuote(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("rq"))
    user_id: str
    send_currency: str
    receive_currency: str
    send_amount: float
    rate: float
    fee: float
    receive_amount: float


class RemittanceTransfer(BaseModel):
    id: str = Field(default_factory=lambda: generate_id("rt"))
    user_id: str
    quote_id: str
    beneficiary_name: str
    beneficiary_iban: Optional[str] = None
    beneficiary_mobile: Optional[str] = None
    status: Literal["created", "processing", "settled", "failed"] = "created"
    created_at: datetime = Field(default_factory=datetime.utcnow)
