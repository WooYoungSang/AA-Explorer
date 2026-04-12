import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_health() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["chain"] == "base"


@pytest.mark.asyncio
async def test_userops_endpoint() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/userops")
    assert response.status_code == 200
    assert response.json()["page"] == 1


@pytest.mark.asyncio
async def test_stats_endpoint() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/stats")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_paymasters_endpoint() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/paymasters")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_smart_accounts_endpoint() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/smart-accounts")
    assert response.status_code == 200
