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
