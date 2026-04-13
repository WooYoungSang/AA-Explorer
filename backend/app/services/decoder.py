from __future__ import annotations

from typing import Any

from web3 import Web3

ENTRYPOINT_V07_ABI = [
    {
        "type": "event",
        "name": "UserOperationEvent",
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "userOpHash", "type": "bytes32"},
            {"indexed": False, "name": "sender", "type": "address"},
            {"indexed": False, "name": "paymaster", "type": "address"},
            {"indexed": False, "name": "nonce", "type": "uint256"},
            {"indexed": False, "name": "success", "type": "bool"},
            {"indexed": False, "name": "actualGasCost", "type": "uint256"},
            {"indexed": False, "name": "actualGasUsed", "type": "uint256"},
        ],
    },
    {
        "type": "event",
        "name": "AccountDeployed",
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "userOpHash", "type": "bytes32"},
            {"indexed": True, "name": "sender", "type": "address"},
            {"indexed": False, "name": "factory", "type": "address"},
            {"indexed": False, "name": "paymaster", "type": "address"},
        ],
    },
    {
        "type": "function",
        "name": "handleOps",
        "stateMutability": "nonpayable",
        "inputs": [
            {
                "name": "ops",
                "type": "tuple[]",
                "components": [
                    {"name": "sender", "type": "address"},
                    {"name": "nonce", "type": "uint256"},
                    {"name": "initCode", "type": "bytes"},
                    {"name": "callData", "type": "bytes"},
                    {"name": "accountGasLimits", "type": "bytes32"},
                    {"name": "preVerificationGas", "type": "uint256"},
                    {"name": "gasFees", "type": "bytes32"},
                    {"name": "paymasterAndData", "type": "bytes"},
                    {"name": "signature", "type": "bytes"},
                ],
            },
            {"name": "beneficiary", "type": "address"},
        ],
        "outputs": [],
    },
]

USER_OPERATION_EVENT_SIGNATURE = (
    "UserOperationEvent(bytes32,address,address,uint256,bool,uint256,uint256)"
)
USER_OPERATION_EVENT_TOPIC0 = Web3.keccak(text=USER_OPERATION_EVENT_SIGNATURE).hex()

_w3 = Web3()
_entrypoint_contract = _w3.eth.contract(abi=ENTRYPOINT_V07_ABI)


def _coerce_int(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        if value.startswith("0x"):
            return int(value, 16)
        return int(value)
    raise TypeError(f"Unsupported integer value: {value!r}")



def _extract_address(blob: bytes) -> str | None:
    if len(blob) < 20:
        return None
    return Web3.to_checksum_address("0x" + blob[:20].hex())



def _decode_transaction_input(
    transaction_input: str | None,
    user_op_index: int = 0,
) -> dict[str, Any]:
    if not transaction_input:
        return {}
    function, arguments = _entrypoint_contract.decode_function_input(transaction_input)
    if function.fn_name != "handleOps":
        return {}
    ops = arguments.get("ops", [])
    if user_op_index >= len(ops):
        return {}
    user_op = ops[user_op_index]
    call_data = user_op.get("callData", b"")
    return {
        "factory": _extract_address(user_op.get("initCode", b"")),
        "paymaster": _extract_address(user_op.get("paymasterAndData", b"")),
        "calldata_hash": Web3.keccak(call_data).hex() if call_data else None,
    }


async def decode_user_op(raw: bytes | dict[str, Any] | None):
    if not raw:
        return None
    if isinstance(raw, (bytes, bytearray)):
        return {"raw_length": len(raw)}
    if not isinstance(raw, dict):
        raise TypeError("raw user op event must be bytes, dict, or None")

    topics = raw.get("topics") or []
    if len(topics) < 2:
        return None
    if str(topics[0]).lower() != USER_OPERATION_EVENT_TOPIC0.lower():
        return None

    payload = raw.get("data")
    if not payload:
        return None

    sender, paymaster, nonce, success, actual_gas_cost, actual_gas_used = _w3.codec.decode(
        ["address", "address", "uint256", "bool", "uint256", "uint256"],
        Web3.to_bytes(hexstr=str(payload)),
    )

    decoded: dict[str, Any] = {
        "user_op_hash": str(topics[1]).lower(),
        "sender": Web3.to_checksum_address(sender),
        "paymaster": Web3.to_checksum_address(paymaster),
        "nonce": nonce,
        "success": success,
        "actual_gas_cost": actual_gas_cost,
        "actual_gas_used": actual_gas_used,
        "tx_hash": str(raw.get("transactionHash") or raw.get("transaction_hash") or "").lower(),
        "block_number": _coerce_int(raw.get("blockNumber") or raw.get("block_number") or 0),
        "log_index": _coerce_int(raw.get("logIndex") or raw.get("log_index") or 0),
        "timestamp": _coerce_int(raw.get("timestamp") or 0),
        "raw_log": raw,
    }

    if raw.get("factory"):
        decoded["factory"] = Web3.to_checksum_address(str(raw["factory"]))

    enriched = _decode_transaction_input(
        raw.get("transactionInput") or raw.get("transaction_input"),
        _coerce_int(raw.get("userOpIndex") or raw.get("user_op_index") or 0),
    )
    decoded.update({key: value for key, value in enriched.items() if value is not None})

    return decoded
