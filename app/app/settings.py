import os

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    kafka_server: str
    schema_server: str
    kafka_compression: str = "gzip"
    registrations_topic: str = "event_registrations"
    broadcaster_events_topic: str = "broadcaster_events"

    db_server: str
    db_port: int = 5432
    db_user: str
    db_password: str
    db_database: str = "postgres"

    class Config:
        env_prefix = "icon_registration_"


if os.environ.get("ENV_FILE", False):
    settings = Settings(_env_file=os.environ.get("ENV_FILE"))
else:
    settings = Settings()
