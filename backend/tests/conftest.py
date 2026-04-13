from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from app.main import app
from app.services.decoder import ENTRYPOINT_V07_ABI, USER_OPERATION_EVENT_TOPIC0
from app.services.pipeline import aggregate_daily_stats, store_user_op
from httpx import ASGITransport, AsyncClient
from web3 import Web3


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
        log_index: int = 0,
        timestamp: int = 1_710_000_000,
        transaction_input: str | None = None,
        user_op_index: int = 0,
        factory: str | None = None,
    ) -> dict[str, object]:
        encoded_data = w3.codec.encode(
            ["address", "address", "uint256", "bool", "uint256", "uint256"],
            [sender, paymaster, nonce, success, actual_gas_cost, actual_gas_used],
        )
        log: dict[str, object] = {
            "address": "0x0000000071727De22E5E9d8BAf0edAc6f37da032",
            "topics": [USER_OPERATION_EVENT_TOPIC0, user_op_hash],
            "data": "0x" + encoded_data.hex(),
            "transactionHash": tx_hash,
            "blockNumber": hex(block_number),
            "logIndex": hex(log_index),
            "timestamp": hex(timestamp),
        }
        if transaction_input is not None:
            log["transactionInput"] = transaction_input
            log["userOpIndex"] = user_op_index
        if factory is not None:
            log["factory"] = factory
        return log

    return _build


@pytest.fixture()
def build_handle_ops_input() -> Callable[..., str]:
    w3 = Web3()
    contract = w3.eth.contract(abi=ENTRYPOINT_V07_ABI)

    def _build(
        *,
        sender: str = "0x" + "22" * 20,
        nonce: int = 7,
        factory: str = "0x" + "55" * 20,
        paymaster: str = "0x" + "33" * 20,
        call_data: bytes = bytes.fromhex("deadbeef"),
        beneficiary: str = "0x" + "66" * 20,
    ) -> str:
        op = (
            sender,
            nonce,
            bytes.fromhex(factory.removeprefix("0x") + "aa55"),
            call_data,
            bytes.fromhex("00" * 32),
            21_000,
            bytes.fromhex("11" * 32),
            bytes.fromhex(paymaster.removeprefix("0x") + "bb66"),
            bytes.fromhex("99" * 65),
        )
        return contract.functions.handleOps([op], beneficiary)._encode_transaction_data()

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
