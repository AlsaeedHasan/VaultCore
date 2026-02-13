from pprint import pprint
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_race_condition_on_withdraw(client, authenticated_user):
    auth_header = authenticated_user["header"]
    user_id = authenticated_user["id"]

    response = client.post(
        "/api/v1/wallets/",
        json={"currency": "EGP", "user_id": user_id},
        headers=auth_header,
    )
    assert response.status_code == 201

    client.post(
        "/api/v1/transaction/deposit",
        json={"amount": 100, "currency": "EGP"},
        headers=auth_header,
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport, base_url="http://test", headers=auth_header
    ) as ac:
        task1 = ac.post(
            "/api/v1/transaction/withdraw",
            json={"amount": 80, "currency": "EGP"},
        )
        task2 = ac.post(
            "/api/v1/transaction/withdraw",
            json={"amount": 80, "currency": "EGP"},
        )

        responses = await asyncio.gather(task1, task2)

    status_codes = [r.status_code for r in responses]

    assert status_codes.count(200) == 1
    assert status_codes.count(400) == 1

    res = client.get("/api/v1/wallets/EGP", headers=auth_header)
    assert float(res.json()["balance"]) == 20.0
