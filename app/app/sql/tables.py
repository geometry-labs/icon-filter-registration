from uuid import uuid4

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class EventRegistrations(Base):
    __tablename__ = "event_registrations"

    reg_id = Column(String, primary_key=True)
    type = Column(String)
    from_address = Column(String)
    to_address = Column(String)
    value = Column(Float)
    keyword = Column(String)
    position = Column(Integer)


class BroadcasterRegistrations(Base):
    __tablename__ = "broadcaster_registrations"

    reg_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, unique=True)
    broadcaster_id = Column(UUID, ForeignKey("broadcasters.broadcaster_id"))
    event_id = Column(String, ForeignKey("event_registrations.reg_id"))
    type = Column(String)
    last_used = Column(DateTime)


class Broadcasters(Base):
    __tablename__ = "broadcasters"

    broadcaster_id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid4, unique=True
    )
    endpoint = Column(String)
    created = Column(DateTime)
