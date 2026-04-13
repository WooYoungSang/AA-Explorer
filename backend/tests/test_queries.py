import pytest
from app.services.queries import (
    get_paymaster_distribution,
    get_smart_account_distribution,
    get_stats,
    get_userop_by_hash,
    get_userops,
)


@pytest.mark.asyncio
async def test_get_userops_returns_paginated_rows(seeded_db_path) -> None:
    items, total = await get_userops(seeded_db_path, page=1, per_page=2)

    assert total == 3
    assert len(items) == 2
    assert items[0]["block_number"] > items[1]["block_number"]
    assert items[0]["user_op_hash"] == "0x" + "13" * 32


@pytest.mark.asyncio
async def test_get_userop_by_hash_returns_single_row(seeded_db_path) -> None:
    item = await get_userop_by_hash("0x" + "12" * 32, seeded_db_path)

    assert item is not None
    assert item["sender"] == "0x" + "33" * 20
    assert item["success"] is False


@pytest.mark.asyncio
async def test_get_stats_returns_daily_rows_and_totals(seeded_db_path) -> None:
    stats = await get_stats(seeded_db_path)

    assert stats["total_ops"] == 3
    assert stats["active_wallets"] == 2
    assert len(stats["daily"]) == 2
    assert stats["daily"][0]["day"] >= stats["daily"][1]["day"]


@pytest.mark.asyncio
async def test_get_paymaster_distribution_computes_percentages(seeded_db_path) -> None:
    items, total_sponsored = await get_paymaster_distribution(seeded_db_path)

    assert total_sponsored == 2
    assert [item["label"] for item in items] == [
        "Coinbase Paymaster",
        "Pimlico Paymaster",
    ]
    assert all(item["percentage"] == 50.0 for item in items)


@pytest.mark.asyncio
async def test_get_smart_account_distribution_uses_distinct_accounts(seeded_db_path) -> None:
    items, total_accounts = await get_smart_account_distribution(seeded_db_path)

    assert total_accounts == 2
    assert items[0]["label"] == "Coinbase Smart Wallet Factory"
    assert items[0]["account_count"] == 1
    assert items[1]["label"] == "Safe Factory"
