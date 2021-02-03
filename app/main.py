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

from app.models import (
    LogEventRegistration,
    LogEventRegistrationMessage,
    RegistrationMessage,
    TransactionRegistration,
    TransactionRegistrationMessage,
)
from app.settings import Settings

s = Settings()
app = FastAPI()
producer = Producer(
    {
        "bootstrap.servers": s.kafka_server,
        "compression.codec": s.kafka_compression,
    }
)

message_schema = {
    "title": s.registrations_topic + "-value",
    "type": "object",
    "properties": {
        "type": {"type": ["string", "null"]},
        "from_address": {"type": ["string", "null"]},
        "to_address": {"type": ["string", "null"]},
        "value": {"type": ["number", "null"]},
        "keyword": {"type": ["string", "null"]},
        "position": {"type": ["integer", "null"]},
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


def nonestr(s):
    if s is None:
        return "None"
    return str(s)


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
    key = registration.address + registration.keyword

    if registration.active:
        # We are performing a REGISTRATION

        # Generate message for registration topic
        msg = LogEventRegistrationMessage(
            to_address=registration.address,
            keyword=registration.keyword,
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
            "SELECT reg_id, to_address, keyword, position FROM registrations WHERE reg_id = '{key}'".format(
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
            "SELECT reg_id, to_address, keyword, position FROM registrations WHERE reg_id = '{key}'".format(
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


@app.post("/register/transaction")
async def register_transaction_event(registration: TransactionRegistration):
    # Generate message key
    key = (
        nonestr(registration.to_address)
        + ":"
        + nonestr(registration.from_address)
        + ":"
        + nonestr(registration.value)
    )

    if registration.active:
        # We are performing a REGISTRATION

        # Generate message for registration topic
        msg = TransactionRegistrationMessage(
            to_address=registration.to_address,
            from_address=registration.from_address,
            value=registration.value,
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
            "SELECT reg_id, from_address, to_address, value FROM registrations WHERE reg_id = '{key}'".format(
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
        if (
            not rows[0][2] == registration.from_address
            and rows[0][3] == registration.to_address
            and rows[0][4] == registration.value
        ):
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
            "SELECT reg_id, from_address, to_address, value FROM registrations WHERE reg_id = '{key}'".format(
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
    cur.execute(
        "SELECT reg_id, to_address, keyword, position FROM registrations WHERE type = 'logevent'"
    )
    rows = cur.fetchall()

    registrations = []

    for row in rows:
        registrations.append(
            LogEventRegistration(
                address=row[1],
                keyword=row[2],
                position=row[3],
                active=True,
            )
        )

    return [item.dict() for item in registrations]


@app.get("/register/transaction")
async def get_transaction_event_registrations():
    cur = con.cursor()
    cur.execute(
        "SELECT reg_id, from_address, to_address, value FROM registrations WHERE type = 'trans'"
    )
    rows = cur.fetchall()

    registrations = []

    for row in rows:
        registrations.append(
            # We use the .construct() method here because we need to skip validation because of None objects
            # We will assume the data has already been validated on insertion, and arguably,
            # this shouldn't be a security issue because we are just returning data to the user that exists in the DB
            TransactionRegistration.construct(
                from_address=row[1],
                to_address=row[2],
                value=row[3],
                active=True,
            )
        )

    return [item.dict() for item in registrations]
