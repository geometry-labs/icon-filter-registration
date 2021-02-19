import os
from json import dumps
from typing import Generator

import pytest
import requests
from fastapi.testclient import TestClient

ENVIRONMENT = os.environ.get("ENVIRONMENT", "local")
if ENVIRONMENT == "local":
    # `.env.local` should be ignored in dockerignore so as to fail in container
    os.environ["ENV_FILE"] = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), ".env.local"
    )

from app.kafka import message_schema
from app.main import app
from app.settings import settings
from app.sql.base import Base, engine


class RequestCache:
    broadcaster_id = None


@pytest.fixture(scope="module")
def client() -> Generator:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session", autouse=True)
def prepare_database():
    Base.metadata.create_all(engine)


@pytest.fixture(scope="session", autouse=True)
def prepare_schema_registry():
    payload = {"schema": message_schema, "schemaType": "JSON"}

    requests.post(settings.SCHEMA_SERVER, dumps(payload))


@pytest.fixture(scope="session", autouse=True)
def prepare_connectors():
    connector_config = {
        "name": "EventRegistrationsSink",
        "config": {
            "connector.class": "io.confluent.connect.jdbc.JdbcSinkConnector",
            "connection.password": "changethis",
            "tasks.max": "1",
            "topics": "event_registrations",
            "value.converter.schema.registry.url": "http://schemaregistry:8081",
            "key.converter.schemas.enable": "false",
            "delete.enabled": "true",
            "auto.evolve": "true",
            "connection.user": "postgres",
            "value.converter.schemas.enable": "true",
            "auto.create": "true",
            "value.converter": "io.confluent.connect.json.JsonSchemaConverter",
            "connection.url": "jdbc:postgresql://postgres:5432/postgres",
            "key.converter": "org.apache.kafka.connect.storage.StringConverter",
            "pk.mode": "record_key",
            "pk.fields": "reg_id",
            "insert.mode": "upsert",
        },
    }

    url = f"http://{os.environ.get('CONNECT_REST_ADVERTISED_HOST_NAME', 'localhost')}:8083/connectors"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    data = dumps(connector_config)

    requests.post(url, headers=headers, data=data)
