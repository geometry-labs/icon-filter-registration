from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    kafka_server: str = Field(..., env="registration_kafka_server")
    schema_server: str = Field(..., env="registration_schema_server")
    kafka_compression: str = Field("gzip", env="registration_kafka_compression")
    registrations_topic: str = Field(
        "event_registrations", env="registration_registrations_topic"
    )
    broadcaster_events_topic: str = Field(
        "broadcaster_events", env="registration_broadcaster_events_topic"
    )
    db_server: str = Field(..., env="registration_db_server")
    db_port: int = Field(5432, env="registration_db_port")
    db_user: str = Field(..., env="registration_db_user")
    db_password: str = Field(..., env="registration_db_password")
    db_database: str = Field("postgres", env="registration_db_database")


settings = Settings()
