import pytest
from app.main import app
from app.models import TransactionRegistration
from app.settings import settings
from httpx import AsyncClient
from tests.conftest import RequestCache

registration = TransactionRegistration(
    to_address="cx0000000000000000000000000000000000000001",
    from_address="cx0000000000000000000000000000000000000002",
)


@pytest.mark.asyncio
async def test_logevent_register():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            settings.API_ENDPOINT_PREFIX + "/transaction/register",
            data=registration.json(),
        )

    RequestCache.tx_id = response.json()["reg_id"]
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_broadcaster_unregister():

    tx_id = RequestCache.tx_id

    unregistration_object = registration
    unregistration_object.reg_id = tx_id

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            settings.API_ENDPOINT_PREFIX + "/transaction/unregister",
            data=unregistration_object.json(),
        )

    assert response.status_code == 200
