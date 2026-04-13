from __future__ import annotations

from pathlib import Path
from typing import Any

import aiosqlite

from app.config import DB_PATH
from app.services.pipeline import ensure_schema


def _row_to_user_op(row: aiosqlite.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["success"] = bool(payload["success"])
    return payload


async def _fetchone(
    db: aiosqlite.Connection,
    query: str,
    params: tuple[Any, ...] = (),
) -> aiosqlite.Row | None:
    cursor = await db.execute(query, params)
    return await cursor.fetchone()


async def get_userops(
    db_path: Path | str = DB_PATH,
    *,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    offset = (page - 1) * per_page
    path = await ensure_schema(db_path)
    async with aiosqlite.connect(path) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            """
            SELECT
                user_op_hash,
                tx_hash,
                block_number,
                log_index,
                timestamp,
                day,
                sender,
                paymaster,
                paymaster_label,
                factory,
                smart_account_label,
                nonce,
                success,
                actual_gas_cost,
                actual_gas_used,
                calldata_hash
            FROM user_ops
            ORDER BY block_number DESC, log_index DESC
            LIMIT ? OFFSET ?
            """,
            (per_page, offset),
        )
        total_row = await _fetchone(db, "SELECT COUNT(*) AS total FROM user_ops")

    total = int(total_row["total"]) if total_row is not None else 0
    return [_row_to_user_op(row) for row in rows], total


async def get_userop_by_hash(
    user_op_hash: str,
    db_path: Path | str = DB_PATH,
) -> dict[str, Any] | None:
    path = await ensure_schema(db_path)
    async with aiosqlite.connect(path) as db:
        db.row_factory = aiosqlite.Row
        row = await _fetchone(
            db,
            """
            SELECT
                user_op_hash,
                tx_hash,
                block_number,
                log_index,
                timestamp,
                day,
                sender,
                paymaster,
                paymaster_label,
                factory,
                smart_account_label,
                nonce,
                success,
                actual_gas_cost,
                actual_gas_used,
                calldata_hash
            FROM user_ops
            WHERE user_op_hash = ?
            """,
            (user_op_hash.lower(),),
        )

    if row is None:
        return None
    return _row_to_user_op(row)


async def get_stats(db_path: Path | str = DB_PATH) -> dict[str, Any]:
    path = await ensure_schema(db_path)
    async with aiosqlite.connect(path) as db:
        db.row_factory = aiosqlite.Row
        daily_rows = await db.execute_fetchall(
            """
            SELECT
                day,
                total_ops,
                success_ops,
                unique_senders,
                sponsored_ops,
                unique_paymasters,
                gas_cost,
                gas_used
            FROM daily_stats
            ORDER BY day DESC
            LIMIT 30
            """
        )
        totals_row = await _fetchone(
            db,
            """
            SELECT
                COUNT(*) AS total_ops,
                COUNT(DISTINCT sender) AS active_wallets
            FROM user_ops
            """,
        )

    return {
        "daily": [dict(row) for row in daily_rows],
        "total_ops": int(totals_row["total_ops"]) if totals_row is not None else 0,
        "active_wallets": int(totals_row["active_wallets"]) if totals_row is not None else 0,
    }


async def get_paymaster_distribution(
    db_path: Path | str = DB_PATH,
) -> tuple[list[dict[str, Any]], int]:
    path = await ensure_schema(db_path)
    async with aiosqlite.connect(path) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            """
            SELECT
                paymaster AS address,
                paymaster_label AS label,
                COUNT(*) AS sponsored_ops
            FROM user_ops
            WHERE paymaster IS NOT NULL AND paymaster != ''
            GROUP BY paymaster, paymaster_label
            ORDER BY sponsored_ops DESC, label ASC
            """
        )
        total_row = await _fetchone(
            db,
            """
            SELECT COUNT(*) AS total_sponsored
            FROM user_ops
            WHERE paymaster IS NOT NULL AND paymaster != ''
            """,
        )

    total_sponsored = int(total_row["total_sponsored"]) if total_row is not None else 0
    items = []
    for row in rows:
        item = dict(row)
        item["percentage"] = (
            round((item["sponsored_ops"] / total_sponsored) * 100, 2)
            if total_sponsored
            else 0.0
        )
        items.append(item)
    return items, total_sponsored


async def get_smart_account_distribution(
    db_path: Path | str = DB_PATH,
) -> tuple[list[dict[str, Any]], int]:
    path = await ensure_schema(db_path)
    async with aiosqlite.connect(path) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall(
            """
            SELECT
                factory,
                smart_account_label AS label,
                COUNT(DISTINCT sender) AS account_count
            FROM user_ops
            GROUP BY factory, smart_account_label
            ORDER BY account_count DESC, label ASC
            """
        )
        total_row = await _fetchone(
            db,
            "SELECT COUNT(DISTINCT sender) AS total_accounts FROM user_ops",
        )

    total_accounts = int(total_row["total_accounts"]) if total_row is not None else 0
    items = []
    for row in rows:
        item = dict(row)
        item["percentage"] = (
            round((item["account_count"] / total_accounts) * 100, 2)
            if total_accounts
            else 0.0
        )
        items.append(item)
    return items, total_accounts
