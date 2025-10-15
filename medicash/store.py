from __future__ import annotations
from typing import Dict, List
from datetime import datetime, timedelta
from .models import User, Session, Card, Transaction, Dispute, MerchantToken, TravelNotice, ShareLink, RemittanceQuote, RemittanceTransfer
from .config import settings
import shortuuid


class InMemoryStore:
    def __init__(self) -> None:
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, Session] = {}
        self.cards: Dict[str, Card] = {}
        self.txns: Dict[str, Transaction] = {}
        self.disputes: Dict[str, Dispute] = {}
        self.tokens: Dict[str, MerchantToken] = {}
        self.travel: Dict[str, TravelNotice] = {}
        self.shares: Dict[str, ShareLink] = {}
        self.quotes: Dict[str, RemittanceQuote] = {}
        self.transfers: Dict[str, RemittanceTransfer] = {}

    # Auth
    def get_or_create_user(self, email: str) -> User:
        for u in self.users.values():
            if u.email == email:
                return u
        user = User(email=email)
        self.users[user.id] = user
        return user

    def create_session(self, user_id: str) -> Session:
        token = f"sess_{shortuuid.uuid()}"
        session = Session(
            token=token,
            user_id=user_id,
            expires_at=datetime.utcnow() + timedelta(minutes=settings.access_token_exp_minutes),
        )
        self.sessions[token] = session
        return session

    def get_session(self, token: str) -> Session | None:
        session = self.sessions.get(token)
        if not session:
            return None
        if session.expires_at < datetime.utcnow():
            del self.sessions[token]
            return None
        return session

    # Cards
    def add_card(self, card: Card) -> Card:
        self.cards[card.id] = card
        return card

    def list_user_cards(self, user_id: str) -> List[Card]:
        return [c for c in self.cards.values() if c.user_id == user_id]

    # Transactions
    def add_txn(self, txn: Transaction) -> Transaction:
        self.txns[txn.id] = txn
        return txn


store = InMemoryStore()