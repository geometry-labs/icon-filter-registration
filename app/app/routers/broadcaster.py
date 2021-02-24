#  Copyright 2021 Geometry Labs, Inc.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from json import dumps

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..kafka import producer
from ..models import (
    BroadcasterID,
    BroadcasterRegistration,
    LogEventRegistration,
    TransactionRegistration,
)
from ..settings import settings
from ..sql import crud
from ..utils import get_db
from .id import unregister_id
from .log_event import register_log_event, unregister_log_event
from .transaction import register_transaction_event, unregister_transaction_event

router = APIRouter()


@router.post("/broadcaster/register", tags=["broadcaster"])
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

        producer.produce(settings.BROADCASTER_EVENTS_TOPIC, value=dumps(msg))

    return {
        "broadcaster_id": broadcaster_registration.broadcaster_id,
        "status": "registered",
    }


@router.post("/broadcaster/unregister", tags=["broadcaster"])
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
        producer.produce(settings.BROADCASTER_EVENTS_TOPIC, value=dumps(msg))
        crud.delete_broadcaster_event_registration(db, reg)
        await unregister_id(found.reg_id, db)

    # Delete broadcaster

    crud.delete_broadcaster(db, registration.broadcaster_id)

    return {"reg_id": registration.broadcaster_id, "status": "unregistered"}


@router.post("/broadcaster/modify", tags=["modify"])
async def modify_broadcaster_registration(
    registration: BroadcasterRegistration,
    db: Session = Depends(get_db),
):
    if not registration.broadcaster_id:
        raise HTTPException(
            400, "Incorrect endpoint for registration. Try '/broadcaster/register'"
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
