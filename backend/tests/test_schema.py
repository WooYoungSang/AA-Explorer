import sqlite3

import pytest
from app.services.pipeline import ensure_schema


@pytest.mark.asyncio
async def test_schema_creates_tables_and_indexes(tmp_path) -> None:
    db_path = tmp_path / "aa_explorer.db"

    await ensure_schema(db_path)

    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        assert {"user_ops", "daily_stats"}.issubset(tables)

        user_op_columns = {row[1] for row in conn.execute("PRAGMA table_info(user_ops)")}
        assert {
            "user_op_hash",
            "tx_hash",
            "block_number",
            "timestamp",
            "day",
            "sender",
            "paymaster",
            "factory",
            "nonce",
            "success",
            "actual_gas_cost",
            "actual_gas_used",
            "paymaster_label",
            "smart_account_label",
        }.issubset(user_op_columns)

        indexes = {row[1] for row in conn.execute("PRAGMA index_list('user_ops')")}
        assert {
            "idx_user_ops_block_number",
            "idx_user_ops_day",
            "idx_user_ops_sender",
            "idx_user_ops_paymaster_label",
            "idx_user_ops_smart_account_label",
        }.issubset(indexes)
