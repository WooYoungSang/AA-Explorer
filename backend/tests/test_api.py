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
async def test_userops_endpoint(api_client) -> None:
    response = await api_client.get("/api/userops?page=1")

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "user_op_hash": "0x" + "13" * 32,
                "tx_hash": "0x" + "cc" * 32,
                "block_number": 202,
                "log_index": 1,
                "timestamp": 1_710_086_450,
                "day": "2024-03-10",
                "sender": "0x" + "22" * 20,
                "paymaster": "0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad",
                "paymaster_label": "Pimlico Paymaster",
                "factory": "0x0ba5ed0c6aa8c49038f819e587e2633c4a9f428a",
                "smart_account_label": "Coinbase Smart Wallet Factory",
                "nonce": 3,
                "success": True,
                "actual_gas_cost": 505,
                "actual_gas_used": 606,
                "calldata_hash": "0x" + "cd" * 32,
            },
            {
                "user_op_hash": "0x" + "12" * 32,
                "tx_hash": "0x" + "bb" * 32,
                "block_number": 201,
                "log_index": 0,
                "timestamp": 1_710_086_400,
                "day": "2024-03-10",
                "sender": "0x" + "33" * 20,
                "paymaster": None,
                "paymaster_label": "Other",
                "factory": "0x5de4839a76cf55d0c90e2061ef4386d962e15ae3",
                "smart_account_label": "Safe Factory",
                "nonce": 2,
                "success": False,
                "actual_gas_cost": 303,
                "actual_gas_used": 404,
                "calldata_hash": "0x" + "bc" * 32,
            },
            {
                "user_op_hash": "0x" + "11" * 32,
                "tx_hash": "0x" + "aa" * 32,
                "block_number": 200,
                "log_index": 0,
                "timestamp": 1_710_000_000,
                "day": "2024-03-09",
                "sender": "0x" + "22" * 20,
                "paymaster": "0x2faeb0760d4230ef2ac21496bb4f0b47d634fd4c",
                "paymaster_label": "Coinbase Paymaster",
                "factory": "0x0ba5ed0c6aa8c49038f819e587e2633c4a9f428a",
                "smart_account_label": "Coinbase Smart Wallet Factory",
                "nonce": 1,
                "success": True,
                "actual_gas_cost": 101,
                "actual_gas_used": 202,
                "calldata_hash": "0x" + "ab" * 32,
            },
        ],
        "total": 3,
        "page": 1,
    }


@pytest.mark.asyncio
async def test_userop_detail_endpoint(api_client) -> None:
    response = await api_client.get("/api/userops/" + ("0x" + "11" * 32))

    assert response.status_code == 200
    assert response.json()["paymaster_label"] == "Coinbase Paymaster"
    assert response.json()["user_op_hash"] == "0x" + "11" * 32


@pytest.mark.asyncio
async def test_userop_detail_endpoint_returns_404_for_missing_hash(api_client) -> None:
    response = await api_client.get("/api/userops/" + ("0x" + "ff" * 32))

    assert response.status_code == 404
    assert response.json() == {"detail": "UserOp not found"}


@pytest.mark.asyncio
async def test_userops_endpoint_rejects_invalid_page(api_client) -> None:
    response = await api_client.get("/api/userops?page=0")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_stats_endpoint(api_client) -> None:
    response = await api_client.get("/api/stats")

    assert response.status_code == 200
    assert response.json() == {
        "daily": [
            {
                "day": "2024-03-10",
                "total_ops": 2,
                "success_ops": 1,
                "unique_senders": 2,
                "sponsored_ops": 1,
                "unique_paymasters": 1,
                "gas_cost": 808,
                "gas_used": 1010,
            },
            {
                "day": "2024-03-09",
                "total_ops": 1,
                "success_ops": 1,
                "unique_senders": 1,
                "sponsored_ops": 1,
                "unique_paymasters": 1,
                "gas_cost": 101,
                "gas_used": 202,
            },
        ],
        "total_ops": 3,
        "active_wallets": 2,
    }


@pytest.mark.asyncio
async def test_paymasters_endpoint(api_client) -> None:
    response = await api_client.get("/api/paymasters")

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "address": "0x2faeb0760d4230ef2ac21496bb4f0b47d634fd4c",
                "label": "Coinbase Paymaster",
                "sponsored_ops": 1,
                "percentage": 50.0,
            },
            {
                "address": "0x3fc91a3afd70395cd496c647d5a6cc9d4b2b7fad",
                "label": "Pimlico Paymaster",
                "sponsored_ops": 1,
                "percentage": 50.0,
            },
        ],
        "total_sponsored": 2,
    }


@pytest.mark.asyncio
async def test_smart_accounts_endpoint(api_client) -> None:
    response = await api_client.get("/api/smart-accounts")

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "factory": "0x0ba5ed0c6aa8c49038f819e587e2633c4a9f428a",
                "label": "Coinbase Smart Wallet Factory",
                "account_count": 1,
                "percentage": 50.0,
            },
            {
                "factory": "0x5de4839a76cf55d0c90e2061ef4386d962e15ae3",
                "label": "Safe Factory",
                "account_count": 1,
                "percentage": 50.0,
            },
        ],
        "total_accounts": 2,
    }
