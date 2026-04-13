from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class APIModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UserOp(APIModel):
    user_op_hash: str
    tx_hash: str
    block_number: int
    log_index: int
    timestamp: int
    day: str
    sender: str
    paymaster: str | None = None
    paymaster_label: str
    factory: str | None = None
    smart_account_label: str
    nonce: int
    success: bool
    actual_gas_cost: int
    actual_gas_used: int
    calldata_hash: str | None = None


class UserOpsResponse(APIModel):
    items: list[UserOp]
    total: int
    page: int


class DailyStat(APIModel):
    day: str
    total_ops: int
    success_ops: int
    unique_senders: int
    sponsored_ops: int
    unique_paymasters: int
    gas_cost: int
    gas_used: int


class StatsResponse(APIModel):
    daily: list[DailyStat]
    total_ops: int
    active_wallets: int


class PaymasterStat(APIModel):
    address: str
    label: str
    sponsored_ops: int
    percentage: float


class PaymastersResponse(APIModel):
    items: list[PaymasterStat]
    total_sponsored: int


class SmartAccountStat(APIModel):
    factory: str | None = None
    label: str
    account_count: int
    percentage: float


class SmartAccountsResponse(APIModel):
    items: list[SmartAccountStat]
    total_accounts: int
