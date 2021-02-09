from json import dumps
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
from app.models import BroadcasterID, LogEventRegistration, TransactionRegistration
from app.settings import settings
from app.sql import crud
from app.utils import acked, get_db

router = APIRouter()


@router.post("/unregister/logEvent", tags=["unregister"])
async def unregister_log_event(
    registration: LogEventRegistration, db: Session = Depends(get_db)
):
    if not registration.reg_id:
        raise HTTPException(400, "You must provide this item's registration ID.")

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


@router.post("/unregister/transaction", tags=["unregister"])
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


@router.post("/unregister/id", tags=["unregister"])
async def unregister_id(
    registration: str,
    db: Session = Depends(get_db),
):
    row = crud.get_event_registration_by_id(db, registration)

    if not row:
        raise HTTPException(400, "Registration ID {} not found.".format(registration))

    if row.type == "trans":
        return await unregister_transaction_event(
            TransactionRegistration(
                reg_id=registration,
                to_address=row.to_address,
                from_address=row.from_address,
                value=row.value,
            ),
            db,
        )

    if row.type == "logevent":
        return await unregister_log_event(
            LogEventRegistration(
                reg_id=registration,
                address=row.to_address,
                keyword=row.keyword,
                position=row.position,
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
            400, "Registration ID {} not found.".format(registration.broadcaster_id)
        )

    # Delete events and broadcaster event registrations

    for reg in rows:
        found = crud.get_event_registration_by_id(db, reg.event_id)
        msg = {
            "event_id": reg.event_id,
            "broadcaster_id": registration.broadcaster_id,
            "active": False,
        }
        producer.produce(settings.broadcaster_events_topic, value=dumps(msg))
        crud.delete_broadcaster_event_registration(db, reg)
        await unregister_id(found.reg_id, db)

    # Delete broadcaster

    crud.delete_broadcaster(db, registration.broadcaster_id)

    return {"reg_id": registration.broadcaster_id, "status": "unregistered"}
