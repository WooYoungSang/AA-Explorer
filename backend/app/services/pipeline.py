from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiosqlite

from app.config import DB_PATH, KNOWN_FACTORIES, KNOWN_PAYMASTERS

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS user_ops (
    user_op_hash TEXT PRIMARY KEY,
    tx_hash TEXT NOT NULL,
    block_number INTEGER NOT NULL,
    log_index INTEGER NOT NULL DEFAULT 0,
    timestamp INTEGER NOT NULL,
    day TEXT NOT NULL,
    sender TEXT NOT NULL,
    paymaster TEXT,
    factory TEXT,
    nonce INTEGER NOT NULL,
    success INTEGER NOT NULL,
    actual_gas_cost INTEGER NOT NULL,
    actual_gas_used INTEGER NOT NULL,
    calldata_hash TEXT,
    paymaster_label TEXT NOT NULL,
    smart_account_label TEXT NOT NULL,
    raw_log TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS daily_stats (
    day TEXT PRIMARY KEY,
    total_ops INTEGER NOT NULL,
    success_ops INTEGER NOT NULL,
    unique_senders INTEGER NOT NULL,
    sponsored_ops INTEGER NOT NULL,
    unique_paymasters INTEGER NOT NULL,
    gas_cost INTEGER NOT NULL,
    gas_used INTEGER NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_ops_block_number ON user_ops(block_number DESC);
CREATE INDEX IF NOT EXISTS idx_user_ops_day ON user_ops(day);
CREATE INDEX IF NOT EXISTS idx_user_ops_sender ON user_ops(sender);
CREATE INDEX IF NOT EXISTS idx_user_ops_paymaster_label ON user_ops(paymaster_label);
CREATE INDEX IF NOT EXISTS idx_user_ops_smart_account_label ON user_ops(smart_account_label);
"""


INSERT_USER_OP_SQL = """
INSERT INTO user_ops (
    user_op_hash,
    tx_hash,
    block_number,
    log_index,
    timestamp,
    day,
    sender,
    paymaster,
    factory,
    nonce,
    success,
    actual_gas_cost,
    actual_gas_used,
    calldata_hash,
    paymaster_label,
    smart_account_label,
    raw_log
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(user_op_hash) DO UPDATE SET
    tx_hash = excluded.tx_hash,
    block_number = excluded.block_number,
    log_index = excluded.log_index,
    timestamp = excluded.timestamp,
    day = excluded.day,
    sender = excluded.sender,
    paymaster = excluded.paymaster,
    factory = excluded.factory,
    nonce = excluded.nonce,
    success = excluded.success,
    actual_gas_cost = excluded.actual_gas_cost,
    actual_gas_used = excluded.actual_gas_used,
    calldata_hash = excluded.calldata_hash,
    paymaster_label = excluded.paymaster_label,
    smart_account_label = excluded.smart_account_label,
    raw_log = excluded.raw_log
"""


AGGREGATE_DAILY_STATS_SQL = """
INSERT INTO daily_stats (
    day,
    total_ops,
    success_ops,
    unique_senders,
    sponsored_ops,
    unique_paymasters,
    gas_cost,
    gas_used,
    updated_at
)
SELECT
    day,
    COUNT(*) AS total_ops,
    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) AS success_ops,
    COUNT(DISTINCT sender) AS unique_senders,
    SUM(CASE WHEN paymaster IS NOT NULL AND paymaster != '' THEN 1 ELSE 0 END) AS sponsored_ops,
    COUNT(
        DISTINCT CASE WHEN paymaster IS NOT NULL AND paymaster != '' THEN paymaster END
    ) AS unique_paymasters,
    COALESCE(SUM(actual_gas_cost), 0) AS gas_cost,
    COALESCE(SUM(actual_gas_used), 0) AS gas_used,
    CURRENT_TIMESTAMP AS updated_at
FROM user_ops
GROUP BY day
ON CONFLICT(day) DO UPDATE SET
    total_ops = excluded.total_ops,
    success_ops = excluded.success_ops,
    unique_senders = excluded.unique_senders,
    sponsored_ops = excluded.sponsored_ops,
    unique_paymasters = excluded.unique_paymasters,
    gas_cost = excluded.gas_cost,
    gas_used = excluded.gas_used,
    updated_at = CURRENT_TIMESTAMP
"""


def normalize_address(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    if value.lower() == "0x0000000000000000000000000000000000000000":
        return None
    return "0x" + value.removeprefix("0x").lower()


_NORMALIZED_PAYMASTERS = {
    normalize_address(address): label for address, label in KNOWN_PAYMASTERS.items()
}
_NORMALIZED_FACTORIES = {
    normalize_address(address): label for address, label in KNOWN_FACTORIES.items()
}


def classify_paymaster(address: str | None) -> str:
    normalized = normalize_address(address)
    if normalized is None:
        return "Other"
    return _NORMALIZED_PAYMASTERS.get(normalized, "Other")



def classify_factory(address: str | None) -> str:
    normalized = normalize_address(address)
    if normalized is None:
        return "Other"
    return _NORMALIZED_FACTORIES.get(normalized, "Other")



def day_from_timestamp(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, tz=UTC).date().isoformat()



def _json_dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str)



def prepare_user_op(record: dict[str, Any]) -> dict[str, Any]:
    timestamp = int(record["timestamp"])
    paymaster = normalize_address(record.get("paymaster"))
    factory = normalize_address(record.get("factory"))
    prepared = {
        "user_op_hash": record["user_op_hash"].lower(),
        "tx_hash": record["tx_hash"].lower(),
        "block_number": int(record["block_number"]),
        "log_index": int(record.get("log_index", 0)),
        "timestamp": timestamp,
        "day": record.get("day") or day_from_timestamp(timestamp),
        "sender": normalize_address(record["sender"]),
        "paymaster": paymaster,
        "factory": factory,
        "nonce": int(record.get("nonce", 0)),
        "success": 1 if bool(record.get("success", False)) else 0,
        "actual_gas_cost": int(record.get("actual_gas_cost", 0)),
        "actual_gas_used": int(record.get("actual_gas_used", 0)),
        "calldata_hash": (record.get("calldata_hash") or None),
        "paymaster_label": record.get("paymaster_label") or classify_paymaster(paymaster),
        "smart_account_label": record.get("smart_account_label") or classify_factory(factory),
        "raw_log": (
            record.get("raw_log")
            if isinstance(record.get("raw_log"), str)
            else _json_dumps(record.get("raw_log") or record)
        ),
    }
    if prepared["sender"] is None:
        raise ValueError("sender is required")
    return prepared


async def ensure_schema(db_path: Path | str = DB_PATH) -> Path:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(path) as db:
        await db.executescript(SCHEMA_SQL)
        await db.commit()
    return path


async def store_user_op(db_path: Path | str, record: dict[str, Any]) -> dict[str, Any]:
    path = await ensure_schema(db_path)
    prepared = prepare_user_op(record)
    async with aiosqlite.connect(path) as db:
        await db.execute(
            INSERT_USER_OP_SQL,
            (
                prepared["user_op_hash"],
                prepared["tx_hash"],
                prepared["block_number"],
                prepared["log_index"],
                prepared["timestamp"],
                prepared["day"],
                prepared["sender"],
                prepared["paymaster"],
                prepared["factory"],
                prepared["nonce"],
                prepared["success"],
                prepared["actual_gas_cost"],
                prepared["actual_gas_used"],
                prepared["calldata_hash"],
                prepared["paymaster_label"],
                prepared["smart_account_label"],
                prepared["raw_log"],
            ),
        )
        await db.commit()
    return prepared


async def aggregate_daily_stats(db_path: Path | str = DB_PATH) -> list[dict[str, Any]]:
    path = await ensure_schema(db_path)
    async with aiosqlite.connect(path) as db:
        await db.execute(AGGREGATE_DAILY_STATS_SQL)
        await db.commit()
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT day, total_ops, success_ops, unique_senders, sponsored_ops, "
            "unique_paymasters, gas_cost, gas_used FROM daily_stats ORDER BY day DESC"
        )
        rows = await cursor.fetchall()
    return [dict(row) for row in rows]
