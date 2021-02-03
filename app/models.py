import re
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel, validator

from app.settings import Settings


class LogEventRegistration(BaseModel):
    address: str
    keyword: str

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
    active: bool


class TransactionRegistration(BaseModel):
    from_address: Optional[str]
    to_address: Optional[str]
    value: Optional[float]
    active: Optional[bool]

    @validator("from_address", "to_address")
    def has_address_prefix(cls, v):
        if not re.search("^cx|^hx", v):
            raise ValueError("ICON addresses must start with 'hx' or 'cx'")
        return v

    @validator("from_address", "to_address")
    def is_correct_length(cls, v):
        if len(v) != 42:
            raise ValueError("ICON addresses must be 42 characters in length")
        return v


class RegistrationMessage(BaseModel):
    type: str
    from_address: Optional[str]
    to_address: Optional[str]
    value: Optional[float]
    keyword: Optional[str]
    position: Optional[int]

    class Config:
        @staticmethod
        def schema_extra(
            schema: Dict[str, Any], model: Type["RegistrationMessage"]
        ) -> None:
            for prop in schema.get("properties", {}).values():
                prop.pop("title", None)
            schema["title"] = Settings().registrations_topic + "-value"


class TransactionRegistrationMessage(RegistrationMessage):
    type = "trans"


class LogEventRegistrationMessage(RegistrationMessage):
    type = "logevent"
    to_address: str
    keyword: str
    position: int
