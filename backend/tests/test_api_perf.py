from time import monotonic

import pytest


@pytest.mark.asyncio
async def test_api_response_under_1s(api_client) -> None:
    for endpoint in [
        "/api/userops",
        "/api/userops/" + ("0x" + "11" * 32),
        "/api/stats",
        "/api/paymasters",
        "/api/smart-accounts",
    ]:
        start = monotonic()
        response = await api_client.get(endpoint)
        elapsed = monotonic() - start

        assert response.status_code == 200
        assert elapsed < 1.0, f"{endpoint} took {elapsed:.4f}s"
