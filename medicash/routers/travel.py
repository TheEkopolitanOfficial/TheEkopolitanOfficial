from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import List
from ..store import store
from ..models import TravelNotice
from .auth import require_auth

router = APIRouter(prefix="/travel", tags=["travel"])


class CreateTravel(BaseModel):
    countries: List[str]
    start_date: datetime
    end_date: datetime


@router.post("")
def create_travel(payload: CreateTravel, user_id: str = Depends(require_auth)):
    t = TravelNotice(user_id=user_id, **payload.model_dump())
    store.travel[t.id] = t
    return t


@router.get("")
def list_travel(user_id: str = Depends(require_auth)):
    return [t for t in store.travel.values() if t.user_id == user_id]
