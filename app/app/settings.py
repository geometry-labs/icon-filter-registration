from pydantic import BaseSettings


class Settings(BaseSettings):
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

    class Config:
        env_prefix = "ICON_REGISTRATION_"
        case_sensitive = True


settings = Settings()
