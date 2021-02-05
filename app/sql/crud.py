from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.sql.tables import BroadcasterRegistrations, Broadcasters, EventRegistrations


def get_event_registrations(db: Session):
    return (
        db.query(EventRegistrations).filter(EventRegistrations.type == "logevent").all()
    )


def get_transaction_registrations(db: Session):
    return db.query(EventRegistrations).filter(EventRegistrations.type == "trans").all()


def get_broadcaster_registrations(db: Session, broadcaster_id: int):
    return (
        db.query(BroadcasterRegistrations)
        .filter(BroadcasterRegistrations.broadcaster_id == broadcaster_id)
        .all()
    )


def get_registration(db: Session, registration_id: str):
    return (
        db.query(EventRegistrations)
        .filter(EventRegistrations.reg_id == registration_id)
        .all()
    )


def new_broadcaster(db: Session, endpoint: str):
    registration = Broadcasters(endpoint=endpoint, created=datetime.now())
    db.add(registration)
    db.commit()
    db.refresh(registration)
    return registration


def new_broadcaster_event_registration(
    db: Session, broadcaster_id: UUID, event_id: str, type: str
):
    registration = BroadcasterRegistrations(
        broadcaster_id=broadcaster_id,
        event_id=event_id,
        type=type,
        last_used=datetime.now(),
    )
    db.add(registration)
    db.commit()
    db.refresh()
    return registration
