import pytest
from app.services.decoder import decode_user_op
from web3 import Web3


@pytest.mark.asyncio
async def test_decoder_handles_empty_input() -> None:
    assert await decode_user_op(b"") is None


@pytest.mark.asyncio
async def test_decoder_normalizes_user_operation_event(build_user_operation_event_log) -> None:
    log = build_user_operation_event_log()

    decoded = await decode_user_op(log)

    assert decoded is not None
    assert decoded["user_op_hash"] == "0x" + "11" * 32
    assert decoded["sender"] == Web3.to_checksum_address("0x" + "22" * 20)
    assert decoded["paymaster"] == Web3.to_checksum_address("0x" + "33" * 20)
    assert decoded["nonce"] == 7
    assert decoded["success"] is True
    assert decoded["actual_gas_cost"] == 1234
    assert decoded["actual_gas_used"] == 5678
    assert decoded["block_number"] == 123
    assert decoded["timestamp"] == 1_710_000_000


@pytest.mark.asyncio
async def test_decoder_enriches_from_handle_ops_input(
    build_handle_ops_input,
    build_user_operation_event_log,
) -> None:
    handle_ops_input = build_handle_ops_input(factory="0x" + "55" * 20, paymaster="0x" + "33" * 20)
    log = build_user_operation_event_log(transaction_input=handle_ops_input)

    decoded = await decode_user_op(log)

    assert decoded is not None
    assert decoded["factory"] == Web3.to_checksum_address("0x" + "55" * 20)
    assert decoded["calldata_hash"] == Web3.keccak(hexstr="0xdeadbeef").hex()
