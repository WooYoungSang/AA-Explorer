from __future__ import annotations

from typing import Any

from web3 import Web3

USER_OPERATION_EVENT_SIGNATURE = (
    "UserOperationEvent(bytes32,address,address,uint256,bool,uint256,uint256)"
)
ACCOUNT_DEPLOYED_SIGNATURE = "AccountDeployed(bytes32,address,address,address)"


def _topic0(signature: str) -> str:
    # web3 7 returns HexBytes.hex() without the 0x prefix; JSON-RPC topics carry it.
    return "0x" + Web3.keccak(text=signature).hex().removeprefix("0x")


USER_OPERATION_EVENT_TOPIC0 = _topic0(USER_OPERATION_EVENT_SIGNATURE)
ACCOUNT_DEPLOYED_TOPIC0 = _topic0(ACCOUNT_DEPLOYED_SIGNATURE)

ZERO_ADDRESS = "0x" + "00" * 20

_w3 = Web3()


def _coerce_int(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        if value.startswith("0x"):
            return int(value, 16)
        return int(value)
    raise TypeError(f"Unsupported integer value: {value!r}")


def _topic_address(topic: Any) -> str:
    return Web3.to_checksum_address("0x" + str(topic)[-40:])


def _address_or_none(address: str) -> str | None:
    checksummed = Web3.to_checksum_address(address)
    return None if checksummed == Web3.to_checksum_address(ZERO_ADDRESS) else checksummed


def _topics(raw: dict[str, Any], expected_topic0: str, count: int) -> list[str] | None:
    topics = [str(topic).lower() for topic in (raw.get("topics") or [])]
    if len(topics) < count or topics[0] != expected_topic0.lower():
        return None
    return topics


def _log_position(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "tx_hash": str(raw.get("transactionHash") or raw.get("transaction_hash") or "").lower(),
        "block_number": _coerce_int(raw.get("blockNumber") or raw.get("block_number") or 0),
        "log_index": _coerce_int(raw.get("logIndex") or raw.get("log_index") or 0),
    }


def decode_account_deployed(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Decode an AccountDeployed log into its userOpHash and factory."""
    topics = _topics(raw, ACCOUNT_DEPLOYED_TOPIC0, 3)
    payload = raw.get("data")
    if topics is None or not payload:
        return None
    factory, _paymaster = _w3.codec.decode(
        ["address", "address"], Web3.to_bytes(hexstr=str(payload))
    )
    return {
        "user_op_hash": topics[1],
        "sender": _topic_address(topics[2]),
        "factory": _address_or_none(factory),
    }


async def decode_user_op(raw: bytes | dict[str, Any] | None):
    """Decode a UserOperationEvent log; other topic0 values return None."""
    if not raw:
        return None
    if isinstance(raw, (bytes, bytearray)):
        return {"raw_length": len(raw)}
    if not isinstance(raw, dict):
        raise TypeError("raw user op event must be bytes, dict, or None")

    topics = _topics(raw, USER_OPERATION_EVENT_TOPIC0, 4)
    payload = raw.get("data")
    if topics is None or not payload:
        return None

    nonce, success, actual_gas_cost, actual_gas_used = _w3.codec.decode(
        ["uint256", "bool", "uint256", "uint256"],
        Web3.to_bytes(hexstr=str(payload)),
    )

    decoded: dict[str, Any] = {
        "user_op_hash": topics[1],
        "sender": _topic_address(topics[2]),
        "paymaster": _address_or_none(_topic_address(topics[3])),
        "nonce": nonce,
        "success": success,
        "actual_gas_cost": actual_gas_cost,
        "actual_gas_used": actual_gas_used,
        "timestamp": _coerce_int(raw.get("timestamp") or 0),
        "factory": None,
        "raw_log": raw,
        **_log_position(raw),
    }
    return decoded
