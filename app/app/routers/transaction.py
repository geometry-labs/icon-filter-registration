from time import sleep
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..kafka import (
    json_serializer,
    key_context,
    producer,
    string_serializer,
    value_context,
)
from ..models import TransactionRegistration, TransactionRegistrationMessage
from ..settings import settings
from ..sql import crud
from ..utils import acked, get_db

router = APIRouter()


@router.post("/transaction/register", tags=["transaction"])
async def register_transaction_event(
    registration: TransactionRegistration, db: Session = Depends(get_db)
):
    # Generate message key
    reg_id = str(uuid4())

    # Generate message for registration topic
    msg = TransactionRegistrationMessage(
        reg_id=reg_id,
        to_address=registration.to_address,
        from_address=registration.from_address,
        value=registration.value,
    )

    # Produce message for registration topic
    producer.produce(
        topic=settings.registrations_topic,
        key=string_serializer(reg_id, key_context),
        value=json_serializer(msg.dict(), value_context),
        callback=acked,
    )

    # Brief sleep to allow Kafka Connect to insert message
    # NOTE: this will probably need to be tuned to ensure race conditions aren't a problem
    sleep(1)

    # Query the DB to check if insert was done correctly
    rows = crud.get_event_registration_by_id_no_404(db, reg_id)

    # Check if query returned a result (i.e. if the transaction was inserted)
    if not rows:
        raise HTTPException(500, "Registration not confirmed. Try again. (NOINSERT)")

    # Check if query returned correct result
    if (
        not rows.to_address == registration.to_address
        and not rows.from_address == registration.from_address
        and not rows.value == registration.value
    ):
        raise HTTPException(500, "Registration not confirmed. Try again. (NOMATCH)")

    return {"reg_id": reg_id, "status": "registered"}


@router.post("/transaction/unregister", tags=["transaction"])
async def unregister_transaction_event(
    registration: TransactionRegistration, db: Session = Depends(get_db)
):

    # Produce message for registration topic
    # NOTE: This is a tombstone record, so the VALUE is NULL
    producer.produce(
        topic=settings.registrations_topic,
        key=string_serializer(registration.reg_id, key_context),
        value=json_serializer(None, value_context),
        callback=acked,
    )

    # Brief sleep to allow Kafka Connect to insert message
    # NOTE: this will probably need to be tuned to ensure race conditions aren't a problem
    sleep(1)

    # Query the DB to check if insert was done correctly
    rows = crud.get_event_registration_by_id_no_404(db, registration.reg_id)

    # Ensure no rows were returned
    if rows:
        raise HTTPException(500, "Unregistration not confirmed. Try again. (NOTOMB)")

    return {"reg_id": registration.reg_id, "status": "unregistered"}


@router.get("/transaction/status", tags=["transaction"])
async def get_transaction_event_registrations(db: Session = Depends(get_db)):
    rows = crud.get_all_transaction_registrations(db)

    registrations = []

    for row in rows:
        registrations.append(
            TransactionRegistration(
                from_address=row[1],
                to_address=row[2],
                value=row[3],
            )
        )

    return [item.dict() for item in registrations]