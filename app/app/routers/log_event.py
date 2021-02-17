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
from ..models import LogEventRegistration, LogEventRegistrationMessage
from ..settings import settings
from ..sql import crud
from ..utils import acked, get_db

router = APIRouter()


@router.post("/logevent/register", tags=["log_event"])
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
        topic=settings.REGISTRATIONS_TOPIC,
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


@router.post("/logevent/unregister", tags=["log_event"])
async def unregister_log_event(
    registration: LogEventRegistration, db: Session = Depends(get_db)
):
    if not registration.reg_id:
        raise HTTPException(400, "You must provide this item's registration ID.")

    # Produce message for registration topic
    # NOTE: This is a tombstone record, so the VALUE is NULL
    producer.produce(
        topic=settings.REGISTRATIONS_TOPIC,
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


@router.get("/logevent/status", tags=["log_event"])
async def get_log_event_registrations(db: Session = Depends(get_db)):
    """
    Method to query current log event registration state.
    :return: List of registration dictionaries
    """

    rows = crud.get_all_event_registrations(db)

    registrations = []

    for row in rows:
        registrations.append(
            LogEventRegistration(
                address=row[1],
                keyword=row[2],
                position=row[3],
            )
        )

    return [item.dict() for item in registrations]
