from json import dumps

from confluent_kafka import Producer
from confluent_kafka.schema_registry.json_schema import JSONSerializer
from confluent_kafka.schema_registry.schema_registry_client import SchemaRegistryClient
from confluent_kafka.serialization import (
    MessageField,
    SerializationContext,
    StringSerializer,
)

from .settings import settings

producer = Producer(
    {
        "bootstrap.servers": settings.kafka_server,
        "compression.codec": settings.kafka_compression,
    }
)

message_schema = {
    "title": settings.registrations_topic + "-value",
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

schema_client = SchemaRegistryClient({"url": settings.schema_server})

json_serializer = JSONSerializer(
    dumps(message_schema), schema_client, conf={"auto.register.schemas": False}
)

string_serializer = StringSerializer()

key_context = SerializationContext(settings.registrations_topic, MessageField.KEY)

value_context = SerializationContext(settings.registrations_topic, MessageField.VALUE)
