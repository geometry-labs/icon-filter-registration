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
        "bootstrap.servers": settings.KAFKA_SERVER,
        "compression.codec": settings.KAFKA_COMPRESSION,
    }
)

message_schema = {
    "title": settings.REGISTRATIONS_TOPIC + "-value",
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

schema_client = SchemaRegistryClient({"url": settings.SCHEMA_SERVER})

json_serializer = JSONSerializer(
    dumps(message_schema), schema_client, conf={"auto.register.schemas": False}
)

string_serializer = StringSerializer()

key_context = SerializationContext(settings.REGISTRATIONS_TOPIC, MessageField.KEY)

value_context = SerializationContext(settings.REGISTRATIONS_TOPIC, MessageField.VALUE)
