from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models import (
    BroadcasterRegistration,
    LogEventRegistration,
    TransactionRegistration,
)
from app.routers.register import register_log_event, register_transaction_event
from app.routers.unregister import unregister_log_event, unregister_transaction_event
from app.sql import crud
from app.utils import get_db

router = APIRouter()


@router.post("/modify/broadcaster", tags=["modify"])
async def modify_broadcaster_registration(
    registration: BroadcasterRegistration,
    db: Session = Depends(get_db),
):
    if not registration.broadcaster_id:
        raise HTTPException(
            400, "Incorrect endpoint for registration. Try '/register/broadcaster/'"
        )

    # Collect current broadcaster x event registrations
    current_registrations = crud.get_broadcaster_registrations(
        db, str(registration.broadcaster_id)
    )

    # Retrieve the item objects of each registration
    current_events = []
    for event in current_registrations:
        res = crud.get_event_registration_by_id(db, event.event_id)
        current_events.append(res)

    # Retrieve item objects of each ID'd object
    event_id_events = []

    if registration.event_ids:
        for event in registration.event_ids:
            res = crud.get_event_registration_by_id(db, event)
            event_id_events.append(res)

    # Create new TransactionRegistration objects from input params
    transaction_events = []

    if registration.transaction_events:
        for event in registration.transaction_events:
            transaction_events.append(
                TransactionRegistration(
                    from_address=event.from_address,
                    to_address=event.to_address,
                    value=event.value,
                )
            )

    # Create new LogEventRegistration objects from input params
    log_events = []

    if registration.log_events:
        for event in registration.log_events:
            log_events.append(
                LogEventRegistration(
                    address=event.address,
                    keyword=event.keyword,
                    position=event.position,
                )
            )

    # Begin matching to eventually form sets for update
    matched_events = []

    # Reduce set of input IDs to determine which ones need to be created
    for item in event_id_events:
        if item in current_events:
            event_id_events.remove(item)
            matched_events.append(item)

    for item in transaction_events:
        if item in current_events:
            transaction_events.remove(item)
            matched_events.append(item)

    for item in log_events:
        if item in current_events:
            log_events.remove(item)
            matched_events.append(item)

    # Determine which items now need to be removed
    to_delete = []

    for item in matched_events:
        if item not in current_events:
            to_delete.append(item)

    # Remove items
    for item in to_delete:
        crud.delete_broadcaster_event_registration(db, item)
        if isinstance(item, TransactionRegistration):
            await unregister_transaction_event(item, db)
        if isinstance(item, LogEventRegistration):
            await unregister_log_event(item, db)

    # Register new items
    for item in event_id_events:
        crud.new_broadcaster_event_registration(
            db, registration.broadcaster_id, item, registration.connection_type
        )

    for item in transaction_events:
        res = await register_transaction_event(item, db)
        crud.new_broadcaster_event_registration(
            db, registration.broadcaster_id, res["reg_id"], registration.connection_type
        )

    for item in log_events:
        res = await register_log_event(item, db)
        crud.new_broadcaster_event_registration(
            db, registration.broadcaster_id, res["reg_id"], registration.connection_type
        )

    return {"reg_id": registration.broadcaster_id, "status": "modified"}
