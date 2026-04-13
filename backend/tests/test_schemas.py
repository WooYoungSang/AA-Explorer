from app.schemas import (
    DailyStat,
    PaymasterStat,
    SmartAccountStat,
    StatsResponse,
    UserOp,
    UserOpsResponse,
)


def test_userops_response_serializes_contract_shape() -> None:
    response = UserOpsResponse(
        items=[
            UserOp(
                user_op_hash="0x" + "11" * 32,
                tx_hash="0x" + "aa" * 32,
                block_number=123,
                log_index=0,
                timestamp=1_710_000_000,
                day="2024-03-09",
                sender="0x" + "22" * 20,
                paymaster="0x" + "33" * 20,
                paymaster_label="Coinbase Paymaster",
                factory="0x" + "44" * 20,
                smart_account_label="Coinbase Smart Wallet Factory",
                nonce=7,
                success=True,
                actual_gas_cost=100,
                actual_gas_used=200,
                calldata_hash="0x" + "55" * 32,
            )
        ],
        total=1,
        page=1,
    )

    payload = response.model_dump()

    assert payload["total"] == 1
    assert payload["page"] == 1
    assert payload["items"][0]["paymaster_label"] == "Coinbase Paymaster"


def test_stats_response_preserves_daily_metrics() -> None:
    response = StatsResponse(
        daily=[
            DailyStat(
                day="2024-03-09",
                total_ops=2,
                success_ops=1,
                unique_senders=2,
                sponsored_ops=1,
                unique_paymasters=1,
                gas_cost=111,
                gas_used=222,
            )
        ],
        total_ops=2,
        active_wallets=2,
    )

    payload = response.model_dump()

    assert payload["daily"][0]["day"] == "2024-03-09"
    assert payload["active_wallets"] == 2


def test_distribution_models_keep_percentage_fields() -> None:
    paymaster = PaymasterStat(
        address="0x" + "33" * 20,
        label="Coinbase Paymaster",
        sponsored_ops=4,
        percentage=80.0,
    )
    smart_account = SmartAccountStat(
        factory="0x" + "44" * 20,
        label="Safe Factory",
        account_count=2,
        percentage=50.0,
    )

    assert paymaster.model_dump()["percentage"] == 80.0
    assert smart_account.model_dump()["account_count"] == 2
