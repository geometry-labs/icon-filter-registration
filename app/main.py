import re
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
from pydantic import BaseModel, BaseSettings, Field, validator


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


class Subject(BaseModel):
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


class Registration(BaseModel):
    subject: Subject
    position: int
    active: bool


class RegistrationMessage(BaseModel):
    address: str
    keyword: str
    position: int


@app.post("/register")
async def register(registration: Registration):
    key = registration.subject.address + registration.subject.keyword
    if registration.active:
        msg = RegistrationMessage(
            address=registration.subject.address,
            keyword=registration.subject.keyword,
            position=registration.position,
        )

        producer.produce(
            topic=s.registrations_topic,
            key=string_serializer(key, key_context),
            value=json_serializer(msg.dict(), value_context),
            callback=acked,
        )

        sleep(0.5)

        cur = con.cursor()
        cur.execute(
            "SELECT reg_id, address, keyword, position from registrations WHERE reg_id = '{key}'".format(
                key=key
            )
        )
        rows = cur.fetchall()

        if not rows:
            raise HTTPException(
                500, "Registration not confirmed. Try again. (NOINSERT)"
            )

        if not rows[0][3] == registration.position:
            raise HTTPException(500, "Registration not confirmed. Try again. (NOMATCH)")

        return "Registered"
    else:
        producer.produce(
            topic=s.registrations_topic,
            key=string_serializer(key, key_context),
            value=json_serializer(None, value_context),
            callback=acked,
        )

        sleep(0.5)

        cur = con.cursor()
        cur.execute(
            "SELECT reg_id, address, keyword, position from registrations WHERE reg_id = '{key}'".format(
                key=key
            )
        )
        rows = cur.fetchall()

        if rows:
            raise HTTPException(
                500, "Unregistration not confirmed. Try again. (NOTOMB)"
            )

        return "Unregistered"


def acked(err, msg):
    if err is not None:
        raise HTTPException(
            500, "Failed to deliver message: %s: %s" % (str(msg), str(err))
        )
