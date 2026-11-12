import inspect
import sqlite3

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
    assert stat["gas_cost"] == "3000"
    assert stat["gas_used"] == 5000


def _rec(n: int, ts: int, *, nonce: int = 1, gas: int = 1, sender: str = "22") -> dict:
    return {
        "user_op_hash": "0x" + f"{n:02x}" * 32, "tx_hash": "0x" + "44" * 32,
        "block_number": n, "log_index": 0, "timestamp": ts, "sender": "0x" + sender * 20,
        "paymaster": None, "factory": None, "nonce": nonce, "success": True,
        "actual_gas_cost": gas, "actual_gas_used": 5,
    }


DAY1, DAY2 = 1_710_000_000, 1_710_100_000  # 2024-03-09, 2024-03-10


def _daily(db_path) -> dict:
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT day, total_ops, gas_cost, updated_at FROM daily_stats")
        return {r[0]: r for r in cursor}


@pytest.mark.asyncio
async def test_store_nonce_above_2_63_roundtrips_exactly(tmp_path) -> None:
    db = tmp_path / "a.db"
    big = 2**256 - 1
    stored = await store_user_op(db, _rec(1, DAY1, nonce=big))
    with sqlite3.connect(db) as conn:
        raw = conn.execute("SELECT nonce, typeof(nonce) FROM user_ops").fetchone()
    assert raw == (str(big), "text")
    assert int(raw[0]) == big and stored["nonce"] == big


@pytest.mark.asyncio
async def test_daily_gas_total_above_2_63_is_exact(tmp_path) -> None:
    db = tmp_path / "a.db"
    a, b = 2**63 + 5, 2**63 + 7
    await store_user_op(db, _rec(1, DAY1, gas=a, sender="22"))
    await store_user_op(db, _rec(2, DAY1, gas=b, sender="23"))
    stats = await aggregate_daily_stats(db)
    assert stats[0]["gas_cost"] == str(a + b)
    assert _daily(db)["2024-03-09"][2] == str(a + b)


@pytest.mark.asyncio
async def test_store_recomputes_only_touched_day(tmp_path) -> None:
    db = tmp_path / "a.db"
    await store_user_op(db, _rec(1, DAY1, gas=10))
    await store_user_op(db, _rec(2, DAY2, gas=20))
    with sqlite3.connect(db) as conn:
        conn.execute("UPDATE daily_stats SET updated_at='SENTINEL' WHERE day='2024-03-09'")
        conn.execute("UPDATE daily_stats SET gas_cost='999' WHERE day='2024-03-09'")
    await store_user_op(db, _rec(3, DAY2, gas=5, sender="23"))
    rows = _daily(db)
    assert rows["2024-03-09"][3] == "SENTINEL" and rows["2024-03-09"][2] == "999"
    assert rows["2024-03-10"][1] == 2 and rows["2024-03-10"][2] == "25"


@pytest.mark.asyncio
async def test_full_aggregate_removes_days_without_user_ops(tmp_path) -> None:
    db = tmp_path / "a.db"
    await store_user_op(db, _rec(1, DAY1))
    await store_user_op(db, _rec(2, DAY2))
    await aggregate_daily_stats(db)
    assert set(_daily(db)) == {"2024-03-09", "2024-03-10"}
    with sqlite3.connect(db) as conn:
        conn.execute("DELETE FROM user_ops WHERE day='2024-03-10'")
    stats = await aggregate_daily_stats(db)
    assert [s["day"] for s in stats] == ["2024-03-09"]
    assert set(_daily(db)) == {"2024-03-09"}


def test_pipeline_signatures_unchanged() -> None:
    assert list(inspect.signature(store_user_op).parameters) == ["db_path", "record"]
    params = inspect.signature(aggregate_daily_stats).parameters
    assert list(params) == ["db_path"] and params["db_path"].default is not inspect.Parameter.empty
