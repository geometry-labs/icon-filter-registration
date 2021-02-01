import re

from pydantic import BaseModel, validator


class LogSubject(BaseModel):
    address: str
    keyword: str

    @validator("address")
    def starts_with_address_indicator(cls, v):
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


class LogEventRegistration(BaseModel):
    subject: LogSubject
    position: int
    active: bool


class LogEventRegistrationMessage(BaseModel):
    address: str
    keyword: str
    position: int
