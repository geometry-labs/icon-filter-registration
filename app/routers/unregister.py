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
    BroadcasterID,
    LogEventRegistration,
    RegistrationID,
    TransactionRegistration,
)
from app.settings import settings
from app.sql import crud
from app.utils import acked, get_db, nonestr

router = APIRouter()


@router.post("/unregister/logEvent", tags=["unregister"])
async def unregister_log_event(
    registration: LogEventRegistration, db: Session = Depends(get_db)
):
    # Generate message key
    key = registration.address + ":" + registration.keyword

    # Produce message for registration topic
    # NOTE: This is a tombstone record, so the VALUE is NULL
    producer.produce(
        topic=settings.registrations_topic,
        key=string_serializer(key, key_context),
        value=json_serializer(None, value_context),
        callback=acked,
    )

    # Brief sleep to allow Kafka Connect to insert message
    # NOTE: this will probably need to be tuned to ensure race conditions aren't a problem
    sleep(0.5)

    # Query the DB to check if insert was done correctly
    rows = crud.get_registration(db, key)

    # Ensure no rows were returned
    if rows:
        raise HTTPException(500, "Unregistration not confirmed. Try again. (NOTOMB)")

    return {"reg_id": key, "status": "unregistered"}


@router.post("/unregister/transaction", tags=["unregister"])
async def unregister_transaction_event(
    registration: TransactionRegistration, db: Session = Depends(get_db)
):
    # Generate message key
    key = (
        nonestr(registration.to_address)
        + ":"
        + nonestr(registration.from_address)
        + ":"
        + nonestr(registration.value)
    )

    # Produce message for registration topic
    # NOTE: This is a tombstone record, so the VALUE is NULL
    producer.produce(
        topic=settings.registrations_topic,
        key=string_serializer(key, key_context),
        value=json_serializer(None, value_context),
        callback=acked,
    )

    # Brief sleep to allow Kafka Connect to insert message
    # NOTE: this will probably need to be tuned to ensure race conditions aren't a problem
    sleep(0.5)

    # Query the DB to check if insert was done correctly
    rows = crud.get_registration(db, key)

    # Ensure no rows were returned
    if rows:
        raise HTTPException(500, "Unregistration not confirmed. Try again. (NOTOMB)")

    return {"reg_id": key, "status": "unregistered"}


@router.post("/unregister/id", tags=["unregister"])
async def unregister_id(registration: RegistrationID, db: Session = Depends(get_db)):
    rows = crud.get_registration(db, registration.reg_id)

    if not rows:
        raise HTTPException(
            400, "Registration ID {} not found.".format(registration.reg_id)
        )

    for row in rows:
        if row.type == "trans":
            return await unregister_transaction_event(
                TransactionRegistration(
                    to_address=row.to_address,
                    from_address=row.from_address,
                    value=row.value,
                ),
                db,
            )

        if row.type == "logevent":
            return await unregister_log_event(
                LogEventRegistration(
                    address=row.to_address, keyword=row.keyword, position=row.position
                ),
                db,
            )


@router.post("/unregister/broadcaster", tags=["unregister"])
async def unregister_broadcaster(
    registration: BroadcasterID, db: Session = Depends(get_db)
):
    rows = crud.get_broadcaster_registrations(db, registration.broadcaster_id)

    if not rows:
        raise HTTPException(
            400, "Registration ID {} not found.".format(registration.reg_id)
        )
