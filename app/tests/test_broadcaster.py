from json import dumps

import pytest
from app.main import app
from app.settings import settings
from httpx import AsyncClient
from tests.conftest import RequestCache

registration_object = {
    "connection_type": "ws",
    "endpoint": "wss://test",
    "transaction_events": [
        {"to_address": "cx0000000000000000000000000000000000000000"}
    ],
}


@pytest.mark.asyncio
async def test_broadcaster_register():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            settings.API_ENDPOINT_PREFIX + "/broadcaster/register",
            data=dumps(registration_object),
        )

    RequestCache.broadcaster_id = response.json()["broadcaster_id"]
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_broadcaster_unregister():

    broadcaster_id = RequestCache.broadcaster_id

    unregistration_object = {"broadcaster_id": broadcaster_id}

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            settings.API_ENDPOINT_PREFIX + "/broadcaster/unregister",
            data=dumps(unregistration_object),
        )

    assert response.status_code == 200
