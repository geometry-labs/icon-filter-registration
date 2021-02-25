import pytest
from app.main import app
from app.models import LogEventRegistration
from app.settings import settings
from httpx import AsyncClient
from tests.conftest import RequestCache

registration = LogEventRegistration(
    address="cx0000000000000000000000000000000000000001",
    keyword="test",
    position=1,
)


@pytest.mark.asyncio
async def test_logevent_register():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            settings.API_ENDPOINT_PREFIX + "/logevent/register",
            data=registration.json(),
        )

    RequestCache.event_id = response.json()["reg_id"]
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_logevent_status():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(settings.API_ENDPOINT_PREFIX + "/logevent/status")

    assert response.status_code == 200
    assert registration.dict() in response.json()


@pytest.mark.asyncio
async def test_broadcaster_unregister():

    event_id = RequestCache.event_id

    unregistration_object = registration
    unregistration_object.reg_id = event_id

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            settings.API_ENDPOINT_PREFIX + "/logevent/unregister",
            data=unregistration_object.json(),
        )

    assert response.status_code == 200
