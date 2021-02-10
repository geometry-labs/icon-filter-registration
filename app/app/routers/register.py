from json import dumps
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
from ..models import (
    BroadcasterRegistration,
    LogEventRegistration,
    LogEventRegistrationMessage,
    TransactionRegistration,
    TransactionRegistrationMessage,
)
from ..settings import settings
from ..sql import crud
from ..utils import acked, get_db

router = APIRouter()


@router.post("/register/logEvent", tags=["register"])
async def register_log_event(
    registration: LogEventRegistration, db: Session = Depends(get_db)
):
    """
    Log event registration handler.
    :param db:
    :param registration: Registration object
    :return: None
    """

    reg_id = str(uuid4())

    # Generate message for registration topic
    msg = LogEventRegistrationMessage(
        to_address=registration.address,
        keyword=registration.keyword,
        position=registration.position,
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
    row = crud.get_event_registration_by_id_no_404(db, reg_id)

    # Check if query returned a result (i.e. if the transaction was inserted)
    if not row:
        raise HTTPException(500, "Registration not confirmed. Try again. (NOINSERT)")

    # Check if query returned correct result
    if (
        not row.to_address == registration.address
        and not row.keyword == registration.keyword
        and not row.position == registration.position
    ):
        raise HTTPException(500, "Registration not confirmed. Try again. (NOMATCH)")

    return {"reg_id": reg_id, "status": "registered"}


@router.post("/register/transaction", tags=["register"])
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


@router.post("/register/broadcaster", tags=["register"])
async def register_broadcaster(
    registration: BroadcasterRegistration,
    db: Session = Depends(get_db),
):
    if registration.broadcaster_id:
        raise HTTPException(
            400, "Incorrect endpoint for modification. Try '/modify/broadcaster/'"
        )

    if not registration.connection_type:
        raise HTTPException(400, "You must specify a connection type.")

    if (
        not registration.event_ids
        and not registration.transaction_events
        and not registration.log_events
    ):
        raise HTTPException(
            400,
            "You must specify one or more of 'event_ids', 'transaction_events', or 'log_events'.",
        )

    events = []

    if registration.event_ids:
        for event in registration.event_ids:
            events.append(event)

    # if new events, register them using the appropriate endpoints

    if registration.transaction_events:
        for event in registration.transaction_events:
            res = await register_transaction_event(
                TransactionRegistration(
                    to_address=event.to_address,
                    from_address=event.from_address,
                    value=event.value,
                ),
                db,
            )
            events.append(res["reg_id"])

    if registration.log_events:
        for event in registration.log_events:
            res = await register_log_event(
                LogEventRegistration(
                    address=event.address,
                    keyword=event.keyword,
                    position=event.position,
                ),
                db,
            )
            events.append(res["reg_id"])

    # create new broadcaster ID

    broadcaster_registration = crud.new_broadcaster(db, registration.endpoint)

    # register all events

    for event in events:
        crud.new_broadcaster_event_registration(
            db,
            broadcaster_registration.broadcaster_id,
            event,
            registration.connection_type,
        )

        msg = {
            "event_id": event,
            "broadcaster_id": str(broadcaster_registration.broadcaster_id),
            "active": True,
        }

        producer.produce(settings.broadcaster_events_topic, value=dumps(msg))

    return {"reg_id": broadcaster_registration.broadcaster_id, "status": "registered"}
