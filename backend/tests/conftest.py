from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pytest
from app.config import ENTRYPOINT_V07
from app.main import app
from app.services.decoder import ACCOUNT_DEPLOYED_TOPIC0, USER_OPERATION_EVENT_TOPIC0
from app.services.pipeline import aggregate_daily_stats, store_user_op
from httpx import ASGITransport, AsyncClient
from web3 import Web3

FIXTURES = Path(__file__).parent / "fixtures"


def _topic_address(address: str) -> str:
    return "0x" + address.removeprefix("0x").lower().rjust(64, "0")


@pytest.fixture()
def real_logs() -> dict[str, object]:
    """UserOperationEvent and AccountDeployed copied from Base mainnet block 56159665."""
    return json.loads((FIXTURES / "base_56159665_logs.json").read_text())


@pytest.fixture()
def build_user_operation_event_log() -> Callable[..., dict[str, object]]:
    w3 = Web3()

    def _build(
        *,
        user_op_hash: str = "0x" + "11" * 32,
        sender: str = "0x" + "22" * 20,
        paymaster: str = "0x" + "33" * 20,
        nonce: int = 7,
        success: bool = True,
        actual_gas_cost: int = 1234,
        actual_gas_used: int = 5678,
        tx_hash: str = "0x" + "44" * 32,
        block_number: int = 123,
        log_index: int = 1,
        removed: bool = False,
    ) -> dict[str, object]:
        encoded_data = w3.codec.encode(
            ["uint256", "bool", "uint256", "uint256"],
            [nonce, success, actual_gas_cost, actual_gas_used],
        )
        return {
            "address": ENTRYPOINT_V07.lower(),
            "topics": [
                USER_OPERATION_EVENT_TOPIC0,
                user_op_hash,
                _topic_address(sender),
                _topic_address(paymaster),
            ],
            "data": "0x" + encoded_data.hex(),
            "transactionHash": tx_hash,
            "blockNumber": hex(block_number),
            "logIndex": hex(log_index),
            "removed": removed,
        }

    return _build


@pytest.fixture()
def build_account_deployed_log() -> Callable[..., dict[str, object]]:
    w3 = Web3()

    def _build(
        *,
        user_op_hash: str = "0x" + "11" * 32,
        sender: str = "0x" + "22" * 20,
        factory: str = "0x" + "55" * 20,
        paymaster: str = "0x" + "00" * 20,
        tx_hash: str = "0x" + "44" * 32,
        block_number: int = 123,
        log_index: int = 0,
    ) -> dict[str, object]:
        encoded_data = w3.codec.encode(["address", "address"], [factory, paymaster])
        return {
            "address": ENTRYPOINT_V07.lower(),
            "topics": [ACCOUNT_DEPLOYED_TOPIC0, user_op_hash, _topic_address(sender)],
            "data": "0x" + encoded_data.hex(),
            "transactionHash": tx_hash,
            "blockNumber": hex(block_number),
            "logIndex": hex(log_index),
            "removed": False,
        }

    return _build


@pytest.fixture()
async def seeded_db_path(tmp_path: Path) -> Path:
    db_path = tmp_path / "aa_explorer.db"
    records = [
        {
            "user_op_hash": "0x" + "11" * 32,
            "tx_hash": "0x" + "aa" * 32,
            "block_number": 200,
            "log_index": 0,
            "timestamp": 1_710_000_000,
            "sender": "0x" + "22" * 20,
            "paymaster": "0x2FAEB0760D4230Ef2aC21496Bb4F0b47D634FD4c",
            "factory": "0x0BA5ED0c6AA8c49038F819E587E2633c4A9F428a",
            "nonce": 1,
            "success": True,
            "actual_gas_cost": 101,
            "actual_gas_used": 202,
            "calldata_hash": "0x" + "ab" * 32,
        },
        {
            "user_op_hash": "0x" + "12" * 32,
            "tx_hash": "0x" + "bb" * 32,
            "block_number": 201,
            "log_index": 0,
            "timestamp": 1_710_086_400,
            "sender": "0x" + "33" * 20,
            "paymaster": None,
            "factory": "0x5de4839a76cf55d0c90e2061ef4386d962E15ae3",
            "nonce": 2,
            "success": False,
            "actual_gas_cost": 303,
            "actual_gas_used": 404,
            "calldata_hash": "0x" + "bc" * 32,
        },
        {
            "user_op_hash": "0x" + "13" * 32,
            "tx_hash": "0x" + "cc" * 32,
            "block_number": 202,
            "log_index": 1,
            "timestamp": 1_710_086_450,
            "sender": "0x" + "22" * 20,
            "paymaster": "0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD",
            "factory": "0x0BA5ED0c6AA8c49038F819E587E2633c4A9F428a",
            "nonce": 3,
            "success": True,
            "actual_gas_cost": 505,
            "actual_gas_used": 606,
            "calldata_hash": "0x" + "cd" * 32,
        },
    ]

    for record in records:
        await store_user_op(db_path, record)
    await aggregate_daily_stats(db_path)
    return db_path


@pytest.fixture()
async def api_client(seeded_db_path: Path) -> AsyncClient:
    original_db_path = getattr(app.state, "db_path", None)
    app.state.db_path = seeded_db_path
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.state.db_path = original_db_path
