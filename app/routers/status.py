from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models import LogEventRegistration, TransactionRegistration
from app.sql import crud
from app.utils import get_db

router = APIRouter()


@router.get("/status/logEvent", tags=["status"])
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


@router.get("/status/transaction", tags=["status"])
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
