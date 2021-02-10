from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..models import LogEventRegistration, TransactionRegistration
from ..sql import crud
from ..utils import get_db
from .log_event import unregister_log_event
from .transaction import unregister_transaction_event

router = APIRouter()


@router.post("/id/unregister", tags=["id"])
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
