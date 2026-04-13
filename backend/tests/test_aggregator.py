import pytest
from app.services.pipeline import aggregate_daily_stats, ensure_schema, store_user_op


@pytest.mark.asyncio
async def test_aggregator_rolls_up_daily_stats(tmp_path) -> None:
    db_path = tmp_path / "aa_explorer.db"
    await ensure_schema(db_path)

    await store_user_op(
        db_path,
        {
            "user_op_hash": "0x" + "11" * 32,
            "tx_hash": "0x" + "44" * 32,
            "block_number": 100,
            "log_index": 0,
            "timestamp": 1_710_000_000,
            "sender": "0x" + "22" * 20,
            "paymaster": "0x" + "33" * 20,
            "factory": "0x" + "55" * 20,
            "nonce": 1,
            "success": True,
            "actual_gas_cost": 1000,
            "actual_gas_used": 2000,
            "calldata_hash": "0x" + "aa" * 32,
            "paymaster_label": "Coinbase Paymaster",
            "smart_account_label": "Coinbase Smart Wallet Factory",
            "raw_log": '{"id":1}',
        },
    )
    await store_user_op(
        db_path,
        {
            "user_op_hash": "0x" + "12" * 32,
            "tx_hash": "0x" + "45" * 32,
            "block_number": 101,
            "log_index": 0,
            "timestamp": 1_710_000_060,
            "sender": "0x" + "23" * 20,
            "paymaster": None,
            "factory": None,
            "nonce": 2,
            "success": False,
            "actual_gas_cost": 2000,
            "actual_gas_used": 3000,
            "calldata_hash": "0x" + "bb" * 32,
            "paymaster_label": "Other",
            "smart_account_label": "Other",
            "raw_log": '{"id":2}',
        },
    )

    daily_stats = await aggregate_daily_stats(db_path)

    assert len(daily_stats) == 1
    stat = daily_stats[0]
    assert stat["total_ops"] == 2
    assert stat["success_ops"] == 1
    assert stat["unique_senders"] == 2
    assert stat["sponsored_ops"] == 1
    assert stat["gas_cost"] == 3000
    assert stat["gas_used"] == 5000
