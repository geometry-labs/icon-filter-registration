from time import sleep

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.kafka import (
    json_serializer,
    key_context,
    producer,
    string_serializer,
    value_context,
)
from app.models import (
    BroadcasterRegistration,
    LogEventRegistration,
    TransactionRegistration,
)
from app.settings import settings
from app.sql import crud
from app.utils import acked, get_db, nonestr

router = APIRouter()


@router.post("/modify/broadcaster")
async def modify_broadcaster_registration(
    registration: BroadcasterRegistration,
    db: Session = Depends(get_db),
):
    if registration.broadcaster_id:

        current_registrations = crud.get_broadcaster_registrations(
            registration.broadcaster_id
        )
        # if registration_id or registrations is specified, we will update those

        new_registrations = []
        if registration.event_ids:
            for event in registration.event_ids:
                res = crud.get_registration(db, event)
                new_registrations.append()

            for reg in current_registrations:
                pass
