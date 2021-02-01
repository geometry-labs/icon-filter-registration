from json import dumps
from time import sleep

import psycopg2
from confluent_kafka import Producer
from confluent_kafka.schema_registry.json_schema import JSONSerializer
from confluent_kafka.schema_registry.schema_registry_client import SchemaRegistryClient
from confluent_kafka.serialization import (
    MessageField,
    SerializationContext,
    StringSerializer,
)
from fastapi import FastAPI, HTTPException
from pydantic import BaseSettings, Field

from app.models import LogEventRegistration, LogEventRegistrationMessage, LogSubject


class Settings(BaseSettings):
    kafka_server: str = Field(..., env="registration_kafka_server")
    schema_server: str = Field(..., env="registration_schema_server")
    kafka_compression: str = Field("gzip", env="registration_kafka_compression")
    registrations_topic: str = Field(
        "registrations", env="registration_registrations_topic"
    )
    db_server: str = Field(..., env="registration_db_server")
    db_port: int = Field(5432, env="registration_db_port")
    db_user: str = Field(..., env="registration_db_user")
    db_password: str = Field(..., env="registration_db_password")
    db_database: str = Field("postgres", env="registration_db_database")


s = Settings()
app = FastAPI()
producer = Producer(
    {
        "bootstrap.servers": s.kafka_server,
        "compression.codec": s.kafka_compression,
    }
)

message_schema = {
    "type": "object",
    "title": s.registrations_topic + "-value",
    "properties": {
        "address": {"type": "string"},
        "keyword": {"type": "string"},
        "position": {"type": "integer"},
    },
}

schema_client = SchemaRegistryClient({"url": s.schema_server})

json_serializer = JSONSerializer(
    dumps(message_schema), schema_client, conf={"auto.register.schemas": False}
)
string_serializer = StringSerializer()

key_context = SerializationContext(s.registrations_topic, MessageField.KEY)
value_context = SerializationContext(s.registrations_topic, MessageField.VALUE)

con = psycopg2.connect(
    database=s.db_database,
    user=s.db_user,
    password=s.db_password,
    host=s.db_server,
    port=s.db_port,
)


def acked(err, msg):
    """
    Kafka production error callback. Used to raise HTTP 500 when message production fails.
    :param err: Kakfa error
    :param msg: Kafka error message
    :return: None
    """
    if err is not None:
        raise HTTPException(
            500, "Failed to deliver message: %s: %s" % (str(msg), str(err))
        )


@app.post("/register/logEvent")
async def register_log_event(registration: LogEventRegistration):
    """
    Log event registration handler.
    :param registration: Registration object
    :return: None
    """

    # Generate message key
    key = registration.subject.address + registration.subject.keyword

    if registration.active:
        # We are performing a REGISTRATION

        # Generate message for registration topic
        msg = LogEventRegistrationMessage(
            address=registration.subject.address,
            keyword=registration.subject.keyword,
            position=registration.position,
        )

        # Produce message for registration topic
        producer.produce(
            topic=s.registrations_topic,
            key=string_serializer(key, key_context),
            value=json_serializer(msg.dict(), value_context),
            callback=acked,
        )

        # Brief sleep to allow Kafka Connect to insert message
        # NOTE: this will probably need to be tuned to ensure race conditions aren't a problem
        sleep(0.5)

        # Query the DB to check if insert was done correctly
        cur = con.cursor()
        cur.execute(
            "SELECT reg_id, address, keyword, position FROM registrations WHERE reg_id = '{key}'".format(
                key=key
            )
        )
        rows = cur.fetchall()

        # Check if query returned a result (i.e. if the transaction was inserted)
        if not rows:
            raise HTTPException(
                500, "Registration not confirmed. Try again. (NOINSERT)"
            )

        # Check if query returned correct result
        if not rows[0][3] == registration.position:
            raise HTTPException(500, "Registration not confirmed. Try again. (NOMATCH)")

        return "Registered"

    else:
        # We are performing a DEREGISTRATION

        # Produce message for registration topic
        # NOTE: This is a tombstone record, so the VALUE is NULL
        producer.produce(
            topic=s.registrations_topic,
            key=string_serializer(key, key_context),
            value=json_serializer(None, value_context),
            callback=acked,
        )

        # Brief sleep to allow Kafka Connect to insert message
        # NOTE: this will probably need to be tuned to ensure race conditions aren't a problem
        sleep(0.5)

        # Query the DB to check if insert was done correctly
        cur = con.cursor()
        cur.execute(
            "SELECT reg_id, address, keyword, position FROM registrations WHERE reg_id = '{key}'".format(
                key=key
            )
        )
        rows = cur.fetchall()

        # Ensure no rows were returned
        if rows:
            raise HTTPException(
                500, "Unregistration not confirmed. Try again. (NOTOMB)"
            )

        return "Unregistered"


@app.get("/register/logEvent")
async def get_log_event_registrations():
    """
    Method to query current log event registration state.
    :return: List of registration dictionaries
    """

    cur = con.cursor()
    cur.execute("SELECT reg_id, address, keyword, position FROM registrations")
    rows = cur.fetchall()

    registrations = []

    for row in rows:
        registrations.append(
            LogEventRegistration(
                subject=LogSubject(address=row[1], keyword=row[2]),
                position=row[3],
                active=True,
            )
        )

    return [item.dict() for item in registrations]
