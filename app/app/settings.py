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

import os

from pydantic import BaseSettings


class Settings(BaseSettings):
    API_ENDPOINT_PREFIX: str = "/api/v1"
    DOCS_ENDPOINT_PREFIX: str = "/api/v1/docs"

    KAFKA_SERVER: str
    SCHEMA_SERVER: str
    KAFKA_COMPRESSION: str = "gzip"
    REGISTRATIONS_TOPIC: str = "event_registrations"
    BROADCASTER_EVENTS_TOPIC: str = "broadcaster_events"
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DATABASE: str = "postgres"
    MAX_CONFIRM_WAIT: int = 10

    class Config:
        env_prefix = "ICON_REGISTRATION_"
        case_sensitive = True


if os.environ.get("ENV_FILE", False):
    settings = Settings(_env_file=os.environ.get("ENV_FILE"))
else:
    settings = Settings()
