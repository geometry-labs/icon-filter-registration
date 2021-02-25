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

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..models import LogEventRegistration, RegistrationID, TransactionRegistration
from ..sql import crud
from ..utils import get_db
from .log_event import unregister_log_event
from .transaction import unregister_transaction_event

router = APIRouter()


@router.post("/id/unregister", tags=["id"])
async def unregister_id(
    registration: RegistrationID,
    db: Session = Depends(get_db),
):
    row = crud.get_event_registration_by_id(db, registration.reg_id)

    if not row:
        raise HTTPException(400, "Registration ID {} not found.".format(registration))

    if row.type == "trans":
        return await unregister_transaction_event(
            TransactionRegistration(
                reg_id=registration.reg_id,
                to_address=row.to_address,
                from_address=row.from_address,
                value=row.value,
            ),
            db,
        )

    if row.type == "logevent":
        return await unregister_log_event(
            LogEventRegistration(
                reg_id=registration.reg_id,
                address=row.to_address,
                keyword=row.keyword,
                position=row.position,
            ),
            db,
        )
