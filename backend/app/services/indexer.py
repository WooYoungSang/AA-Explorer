from __future__ import annotations

import asyncio
import inspect
import json
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
import websockets

from app.config import DB_PATH, ENTRYPOINT_V07
from app.services.decoder import USER_OPERATION_EVENT_TOPIC0, decode_user_op
from app.services.pipeline import aggregate_daily_stats, store_user_op

BACKOFF_SCHEDULE_SECONDS = (1, 2, 4, 8, 16)
JsonDict = dict[str, Any]


async def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


async def _fetch_logs_via_http(rpc_https: str, lookback_blocks: int = 20) -> list[JsonDict]:
    async with httpx.AsyncClient(timeout=10) as client:
        latest_response = await client.post(
            rpc_https,
            json={"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber", "params": []},
        )
        latest_response.raise_for_status()
        latest_block = int(latest_response.json()["result"], 16)
        from_block = max(latest_block - lookback_blocks + 1, 0)
        logs_response = await client.post(
            rpc_https,
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "eth_getLogs",
                "params": [
                    {
                        "address": ENTRYPOINT_V07,
                        "topics": [USER_OPERATION_EVENT_TOPIC0],
                        "fromBlock": hex(from_block),
                        "toBlock": hex(latest_block),
                    }
                ],
            },
        )
        logs_response.raise_for_status()
        return logs_response.json().get("result", [])


async def _persist_event(db_path: str, raw_event: JsonDict) -> dict[str, Any] | None:
    decoded = await decode_user_op(raw_event)
    if decoded is None:
        return None
    stored = await store_user_op(db_path, decoded)
    await aggregate_daily_stats(db_path)
    return stored


async def start_indexer(
    rpc_wss: str,
    rpc_https: str | None = None,
    *,
    db_path: str = str(DB_PATH),
    websocket_factory: Callable[[str], Any] | None = None,
    http_get_logs: Callable[[str], Awaitable[list[JsonDict]] | list[JsonDict]] | None = None,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    stop_after_events: int | None = None,
    max_retries: int = len(BACKOFF_SCHEDULE_SECONDS),
) -> dict[str, Any]:
    connector = websocket_factory or websockets.connect
    state: dict[str, Any] = {
        "status": "running",
        "rpc_wss": rpc_wss,
        "rpc_https": rpc_https,
        "processed": 0,
        "retries": 0,
        "fallback_used": False,
    }

    subscribe_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_subscribe",
        "params": ["logs", {"address": ENTRYPOINT_V07, "topics": [USER_OPERATION_EVENT_TOPIC0]}],
    }

    last_error: str | None = None
    for attempt in range(max_retries):
        try:
            async with connector(rpc_wss) as websocket:
                await websocket.send(json.dumps(subscribe_request))
                while True:
                    message = json.loads(await websocket.recv())
                    event = message.get("params", {}).get("result")
                    if event is None:
                        continue
                    stored = await _persist_event(db_path, event)
                    if stored is None:
                        continue
                    state["processed"] += 1
                    if stop_after_events is not None and state["processed"] >= stop_after_events:
                        state["status"] = "completed"
                        return state
        except Exception as exc:  # noqa: BLE001
            state["retries"] = attempt + 1
            last_error = str(exc)
            await sleep(BACKOFF_SCHEDULE_SECONDS[min(attempt, len(BACKOFF_SCHEDULE_SECONDS) - 1)])

    if rpc_https is None:
        state["status"] = "failed"
        state["last_error"] = last_error or "wss_failed_without_http_fallback"
        return state

    state["fallback_used"] = True
    fetch_logs = http_get_logs or _fetch_logs_via_http
    try:
        logs = await _maybe_await(fetch_logs(rpc_https))
        for raw_event in logs:
            stored = await _persist_event(db_path, raw_event)
            if stored is not None:
                state["processed"] += 1
        state["status"] = "completed"
        return state
    except Exception as exc:  # noqa: BLE001
        state["status"] = "failed"
        state["last_error"] = str(exc)
        state["kill_condition_warning"] = (
            "Fallback HTTP ingestion failed after repeated WSS failures; "
            "evaluate project kill condition"
        )
        return state
