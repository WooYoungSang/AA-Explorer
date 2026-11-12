import pytest
from app.services.decoder import (
    ACCOUNT_DEPLOYED_TOPIC0,
    USER_OPERATION_EVENT_TOPIC0,
    decode_account_deployed,
    decode_user_op,
)
from web3 import Web3

REAL_HASH = "0x612b51bf0ff01b0fb5185b3ed960c32de68c698e6376d127b0b36d9023f206cb"
REAL_SENDER = "0x10d8D46895258665d2C883FD22590e57F97bc6e8"
REAL_FACTORY = "0x4e1DCf7AD4e460CfD30791CCC4F9c8a4f820ec67"
REAL_NONCE = 1349922108732410557691099456300747061872206831688280440832


def _real(real_logs, topic0):
    return next(log for log in real_logs["logs"] if log["topics"][0] == topic0)


@pytest.mark.asyncio
async def test_decoder_handles_empty_input() -> None:
    assert await decode_user_op(b"") is None


def test_topic0_constants_have_0x_prefix() -> None:
    assert USER_OPERATION_EVENT_TOPIC0 == (
        "0x49628fd1471006c1482da88028e9ce4dbb080b815c9b0344d39e5a8e6ec1419f"
    )
    assert ACCOUNT_DEPLOYED_TOPIC0 == (
        "0xd51a9c61267aa6196961883ecf5ff2da6619c37dac0fa92122513fb32c032d2d"
    )


@pytest.mark.asyncio
async def test_real_log_fixture_decodes(real_logs) -> None:
    decoded = await decode_user_op(_real(real_logs, USER_OPERATION_EVENT_TOPIC0))

    assert decoded is not None
    assert decoded["user_op_hash"] == REAL_HASH
    assert decoded["sender"] == REAL_SENDER
    assert decoded["paymaster"] is None
    assert decoded["success"] is True
    assert decoded["actual_gas_cost"] == 0
    assert decoded["actual_gas_used"] == 944265
    assert decoded["block_number"] == 56159665
    assert decoded["log_index"] == 0x40


@pytest.mark.asyncio
async def test_large_nonce_decodes_as_int(real_logs) -> None:
    decoded = await decode_user_op(_real(real_logs, USER_OPERATION_EVENT_TOPIC0))

    assert decoded["nonce"] == REAL_NONCE
    assert isinstance(decoded["nonce"], int)
    assert decoded["nonce"] >= 2**63


@pytest.mark.asyncio
async def test_paymaster_and_data_words_decode(build_user_operation_event_log) -> None:
    decoded = await decode_user_op(
        build_user_operation_event_log(nonce=7, success=False, actual_gas_cost=9, actual_gas_used=8)
    )

    assert decoded["paymaster"] == Web3.to_checksum_address("0x" + "33" * 20)
    assert (decoded["nonce"], decoded["success"]) == (7, False)
    assert (decoded["actual_gas_cost"], decoded["actual_gas_used"]) == (9, 8)


@pytest.mark.asyncio
async def test_zero_paymaster_is_none(build_user_operation_event_log) -> None:
    decoded = await decode_user_op(build_user_operation_event_log(paymaster="0x" + "00" * 20))

    assert decoded["paymaster"] is None


@pytest.mark.asyncio
async def test_other_topic0_returns_none(build_user_operation_event_log) -> None:
    log = build_user_operation_event_log()
    log["topics"][0] = "0x" + "ab" * 32

    assert await decode_user_op(log) is None


def test_factory_from_account_deployed(real_logs) -> None:
    deployed = decode_account_deployed(_real(real_logs, ACCOUNT_DEPLOYED_TOPIC0))

    assert deployed == {"user_op_hash": REAL_HASH, "sender": REAL_SENDER, "factory": REAL_FACTORY}


@pytest.mark.asyncio
async def test_factory_none_without_deployed(real_logs) -> None:
    decoded = await decode_user_op(_real(real_logs, USER_OPERATION_EVENT_TOPIC0))

    assert decoded["factory"] is None


def test_two_userops_in_one_tx_own_factory(build_account_deployed_log) -> None:
    first = decode_account_deployed(
        build_account_deployed_log(user_op_hash="0x" + "a1" * 32, factory="0x" + "f1" * 20)
    )
    second = decode_account_deployed(
        build_account_deployed_log(user_op_hash="0x" + "a2" * 32, factory="0x" + "f2" * 20)
    )

    assert first["factory"] == Web3.to_checksum_address("0x" + "f1" * 20)
    assert second["factory"] == Web3.to_checksum_address("0x" + "f2" * 20)
