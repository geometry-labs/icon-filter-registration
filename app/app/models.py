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

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Type
from uuid import UUID

from pydantic import BaseModel, validator

from .settings import settings


class LogEventRegistration(BaseModel):
    reg_id: str
    address: str
    keyword: str
    reg_id: Optional[str]

    @validator("address")
    def has_contract_prefix(cls, v):
        if not re.search("^cx", v):
            raise ValueError("Contract addresses must start with 'cx'")
        return v

    @validator("address")
    def is_correct_length(cls, v):
        if len(v) != 42:
            raise ValueError("Contract addresses must be 42 characters in length")
        return v

    @validator("address")
    def not_cx0(cls, v):
        if v == "cx0000000000000000000000000000000000000000":
            raise ValueError(
                "Cannot register events for cx0000000000000000000000000000000000000000"
            )
        return v

    position: int


class TransactionRegistration(BaseModel):
    from_address: Optional[str]
    to_address: Optional[str]
    value: Optional[float]
    reg_id: Optional[str]

    @validator("from_address", "to_address")
    def has_address_prefix(cls, v):
        if type(v) is str and not re.search("^cx|^hx", v):
            raise ValueError("ICON addresses must start with 'hx' or 'cx'")
        return v

    @validator("from_address", "to_address")
    def is_correct_length(cls, v):
        if type(v) is str and len(v) != 42:
            raise ValueError("ICON addresses must be 42 characters in length")
        return v


class RegistrationMessage(BaseModel):
    type: str
    from_address: Optional[str]
    to_address: Optional[str]
    value: Optional[float]
    keyword: Optional[str]
    position: Optional[int]
    reg_id: Optional[str]

    class Config:
        orm_mode = True

        @staticmethod
        def schema_extra(
            schema: Dict[str, Any], model: Type["RegistrationMessage"]
        ) -> None:
            for prop in schema.get("properties", {}).values():
                prop.pop("title", None)
            schema["title"] = settings.REGISTRATIONS_TOPIC + "-value"


class TransactionRegistrationMessage(RegistrationMessage):
    type = "trans"


class LogEventRegistrationMessage(RegistrationMessage):
    type = "logevent"
    to_address: str
    keyword: str
    position: int


class BroadcasterRegistration(BaseModel):
    broadcaster_id: Optional[UUID]
    connection_type: str
    endpoint: str
    event_ids: Optional[List[str]]
    transaction_events: Optional[List[TransactionRegistration]]
    log_events: Optional[List[LogEventRegistration]]


class BroadcasterRegistrationID(BaseModel):
    broadcaster_id: UUID
    endpoint: str
    created: datetime

    class Config:
        orm_mode = True


class RegistrationConfirmation(BaseModel):
    reg_id: str
    status: str


class RegistrationID(BaseModel):
    reg_id: str


class BroadcasterID(BaseModel):
    broadcaster_id: str
