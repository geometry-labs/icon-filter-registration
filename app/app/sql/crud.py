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

from datetime import datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .tables import BroadcasterRegistrations, Broadcasters, EventRegistrations


def get_all_event_registrations(db: Session):
    return (
        db.query(EventRegistrations).filter(EventRegistrations.type == "logevent").all()
    )


def get_all_transaction_registrations(db: Session):
    return db.query(EventRegistrations).filter(EventRegistrations.type == "trans").all()


def get_event_registration_by_id(db: Session, reg_id: str):
    res = (
        db.query(EventRegistrations).filter(EventRegistrations.reg_id == reg_id).first()
    )

    if not res:
        raise HTTPException(404, "No registrations with ID {} found.".format(reg_id))

    return res


def get_event_registration_by_id_no_404(db: Session, reg_id: str):
    res = (
        db.query(EventRegistrations).filter(EventRegistrations.reg_id == reg_id).first()
    )

    return res


def get_broadcaster_registrations(db: Session, broadcaster_id: str):
    res = (
        db.query(BroadcasterRegistrations)
        .filter(BroadcasterRegistrations.broadcaster_id == broadcaster_id)
        .all()
    )

    if not res:
        raise HTTPException(
            404,
            "No registrations for broadcaster with ID {} found.".format(broadcaster_id),
        )

    return res


def get_broadcaster(db: Session, broadcaster_id: UUID):
    res = (
        db.query(Broadcasters)
        .filter(Broadcasters.broadcaster_id == broadcaster_id)
        .first()
    )

    if not res:
        raise HTTPException(
            404, "Broadcaster with ID {} not found.".format(broadcaster_id)
        )

    return res


def new_broadcaster(db: Session, endpoint: str):
    registration = Broadcasters(endpoint=endpoint, created=datetime.now())
    db.add(registration)
    db.commit()
    db.refresh(registration)

    return registration


def delete_broadcaster(db: Session, reg_id: str):
    registration = get_broadcaster(db, reg_id)
    db.delete(registration)
    db.commit()


def new_broadcaster_event_registration(
    db: Session, broadcaster_id: UUID, event_id: str, conn_type: str
):
    registration = BroadcasterRegistrations(
        broadcaster_id=str(broadcaster_id),
        event_id=event_id,
        type=conn_type,
        last_used=datetime.now(),
    )
    db.add(registration)
    db.commit()
    db.refresh(registration)

    return registration


def delete_broadcaster_event_registration(
    db: Session, registration: BroadcasterRegistrations
):
    db.delete(registration)
    db.commit()
