from json import dumps

import pytest
from app.main import app
from app.models import LogEventRegistration, RegistrationID, TransactionRegistration
from app.settings import settings
from httpx import AsyncClient

transaction = TransactionRegistration(
    to_address="cx0000000000000000000000000000000000000001",
    from_address="cx0000000000000000000000000000000000000002",
)

registration = LogEventRegistration(
    address="cx0000000000000000000000000000000000000001",
    keyword="test",
    position=1,
)


@pytest.mark.asyncio
async def test_logevent_unregister_by_id():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            settings.API_ENDPOINT_PREFIX + "/logevent/register",
            data=registration.json(),
        )

    reg_id = response.json()["reg_id"]

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            settings.API_ENDPOINT_PREFIX + "/id/unregister",
            data=RegistrationID(reg_id=reg_id).json(),
        )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_transaction_unregister_by_id():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            settings.API_ENDPOINT_PREFIX + "/transaction/register",
            data=transaction.json(),
        )

    reg_id = response.json()["reg_id"]

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            settings.API_ENDPOINT_PREFIX + "/id/unregister",
            data=RegistrationID(reg_id=reg_id).json(),
        )

    assert response.status_code == 200
