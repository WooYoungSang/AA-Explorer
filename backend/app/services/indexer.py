from __future__ import annotations

import asyncio
import inspect
import json
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

import aiosqlite
import httpx
import websockets

from app.config import DB_PATH, ENTRYPOINT_V07
from app.services.decoder import (
    ACCOUNT_DEPLOYED_TOPIC0,
    USER_OPERATION_EVENT_TOPIC0,
    decode_account_deployed,
    decode_user_op,
)
from app.services.pipeline import aggregate_daily_stats, store_user_op

BACKOFF_SCHEDULE_SECONDS = (1, 2, 4, 8, 16)
INITIAL_LOG_SPAN = 2_000
MAX_CACHED_BLOCKS = 512
MAX_PENDING_FACTORIES = 1_000
JsonDict = dict[str, Any]
RpcCall = Callable[[str, list[Any]], Awaitable[Any] | Any]

STATE_SQL = """
CREATE TABLE IF NOT EXISTS indexer_state (
    entrypoint TEXT PRIMARY KEY,
    last_block INTEGER NOT NULL
)
"""


def log_filter(**extra: Any) -> JsonDict:
    """Filter shared by eth_subscribe and eth_getLogs (both events, v0.7 address)."""
    return {
        "address": ENTRYPOINT_V07,
        "topics": [[USER_OPERATION_EVENT_TOPIC0, ACCOUNT_DEPLOYED_TOPIC0]],
        **extra,
    }


async def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


def _http_rpc(rpc_https: str) -> RpcCall:
    async def call(method: str, params: list[Any]) -> Any:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                rpc_https,
                json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
            )
            response.raise_for_status()
            body = response.json()
        if "error" in body:
            raise RuntimeError(f"{method} failed: {body['error']}")
        return body["result"]

    return call


async def _load_last_block(db_path: str) -> int | None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(db_path) as db:
        await db.execute(STATE_SQL)
        cursor = await db.execute(
            "SELECT last_block FROM indexer_state WHERE entrypoint = ?", (ENTRYPOINT_V07,)
        )
        row = await cursor.fetchone()
        await db.commit()
    return None if row is None else int(row[0])


async def _save_last_block(db_path: str, block: int) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(STATE_SQL)
        await db.execute(
            "INSERT INTO indexer_state (entrypoint, last_block) VALUES (?, ?) "
            "ON CONFLICT(entrypoint) DO UPDATE "
            "SET last_block = MAX(last_block, excluded.last_block)",
            (ENTRYPOINT_V07, block),
        )
        await db.commit()


async def _delete_user_op(db_path: str, user_op_hash: str) -> None:
    async with aiosqlite.connect(db_path) as db:
        try:
            await db.execute("DELETE FROM user_ops WHERE user_op_hash = ?", (user_op_hash.lower(),))
        except aiosqlite.OperationalError:  # nothing stored yet, so nothing to remove
            return
        await db.commit()
    await aggregate_daily_stats(db_path)


class _Ingestor:
    def __init__(self, db_path: str, rpc: RpcCall | None) -> None:
        self.db_path = db_path
        self.rpc = rpc
        self.timestamps: dict[int, int] = {}
        self.factories: dict[str, str | None] = {}
        self.processed = 0
        self.gap_from: int | None = None

    async def block_timestamp(self, block_number: int) -> int:
        if block_number not in self.timestamps:
            if self.rpc is None:
                raise RuntimeError("an HTTP RPC is required to read block timestamps")
            block = await _maybe_await(self.rpc("eth_getBlockByNumber", [hex(block_number), False]))
            timestamp = int((block or {}).get("timestamp") or "0x0", 16)
            if timestamp <= 0:
                raise RuntimeError(f"block {block_number} has no timestamp")
            if len(self.timestamps) >= MAX_CACHED_BLOCKS:
                self.timestamps.pop(next(iter(self.timestamps)))
            self.timestamps[block_number] = timestamp
        return self.timestamps[block_number]

    def remember_factory(self, raw: JsonDict) -> None:
        deployed = decode_account_deployed(raw)
        if deployed is None:
            return
        if raw.get("removed"):
            self.factories.pop(deployed["user_op_hash"], None)
            return
        if len(self.factories) >= MAX_PENDING_FACTORIES:
            self.factories.pop(next(iter(self.factories)))
        self.factories[deployed["user_op_hash"]] = deployed["factory"]

    async def store_event(self, raw: JsonDict) -> bool:
        decoded = await decode_user_op(raw)
        if decoded is None:
            return False
        user_op_hash = str(decoded["user_op_hash"])
        if raw.get("removed"):
            await _delete_user_op(self.db_path, user_op_hash)
            return False
        decoded["factory"] = self.factories.pop(user_op_hash, None)
        decoded["timestamp"] = await self.block_timestamp(int(decoded["block_number"]))
        await store_user_op(self.db_path, decoded)
        await aggregate_daily_stats(self.db_path)
        self.processed += 1
        return True

    async def handle_log(self, raw: JsonDict) -> None:
        topics = raw.get("topics") or []
        if topics and str(topics[0]).lower() == ACCOUNT_DEPLOYED_TOPIC0:
            self.remember_factory(raw)
        else:
            await self.store_event(raw)

    async def handle_batch(self, logs: list[JsonDict]) -> None:
        # One pass in chain order: within a transaction every AccountDeployed precedes the
        # UserOperationEvents, so pending factories never outgrow a transaction.
        for raw in sorted(
            logs, key=lambda log: (int(log["blockNumber"], 16), int(log["logIndex"], 16))
        ):
            await self.handle_log(raw)

    async def fetch_range(self, cursor: int, head: int) -> None:
        """Fetch and handle logs for cursor..head, halving the span when the node refuses."""
        assert self.rpc is not None
        span = INITIAL_LOG_SPAN
        while cursor <= head:
            end = min(cursor + span - 1, head)
            try:
                logs = await _maybe_await(
                    self.rpc(
                        "eth_getLogs",
                        [log_filter(fromBlock=hex(cursor), toBlock=hex(end))],
                    )
                )
            except Exception:  # noqa: BLE001 - node refused the range, retry with half
                if span == 1:
                    raise
                span = max(span // 2, 1)
                continue
            await self.handle_batch(logs)
            await _save_last_block(self.db_path, end)
            cursor = end + 1

    async def backfill(self) -> None:
        """Fetch logs from the last fully processed block up to the head."""
        if self.rpc is None:
            return
        head = int(await _maybe_await(self.rpc("eth_blockNumber", [])), 16)
        self.gap_from = head + 1
        last = await _load_last_block(self.db_path)
        if last is None:  # first start: nothing before it is ever fetched
            await _save_last_block(self.db_path, head)
            return
        await self.fetch_range(last, head)

    async def fill_subscription_gap(self, first_block: int) -> None:
        """Fetch blocks between the HTTP head and the first subscription log, once per connect."""
        gap_from, self.gap_from = self.gap_from, None
        if gap_from is not None and first_block > gap_from and self.rpc is not None:
            await self.fetch_range(gap_from, first_block - 1)


async def start_indexer(
    rpc_wss: str,
    rpc_https: str | None = None,
    *,
    db_path: str = str(DB_PATH),
    websocket_factory: Callable[[str], Any] | None = None,
    rpc_call: RpcCall | None = None,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    stop_after_events: int | None = None,
    max_retries: int = len(BACKOFF_SCHEDULE_SECONDS),
) -> dict[str, Any]:
    connector = websocket_factory or websockets.connect
    rpc = rpc_call or (_http_rpc(rpc_https) if rpc_https else None)
    ingestor = _Ingestor(db_path, rpc)
    state: dict[str, Any] = {
        "status": "running",
        "rpc_wss": rpc_wss,
        "rpc_https": rpc_https,
        "processed": 0,
        "retries": 0,
        "fallback_used": False,
    }

    def reached_limit() -> bool:
        state["processed"] = ingestor.processed
        return stop_after_events is not None and ingestor.processed >= stop_after_events

    subscribe_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_subscribe",
        "params": ["logs", log_filter()],
    }

    last_error: str | None = None
    for attempt in range(max_retries):
        try:
            async with connector(rpc_wss) as websocket:
                await websocket.send(json.dumps(subscribe_request))
                await ingestor.backfill()
                if reached_limit():
                    state["status"] = "completed"
                    return state
                while True:
                    message = json.loads(await websocket.recv())
                    event = message.get("params", {}).get("result")
                    if event is None:
                        continue
                    if event.get("blockNumber"):
                        await ingestor.fill_subscription_gap(int(event["blockNumber"], 16))
                    await ingestor.handle_log(event)
                    if event.get("removed") is not True and event.get("blockNumber"):
                        await _save_last_block(db_path, int(event["blockNumber"], 16) - 1)
                    if reached_limit():
                        state["status"] = "completed"
                        return state
        except Exception as exc:  # noqa: BLE001
            state["retries"] = attempt + 1
            state["processed"] = ingestor.processed
            last_error = str(exc)
            await sleep(BACKOFF_SCHEDULE_SECONDS[min(attempt, len(BACKOFF_SCHEDULE_SECONDS) - 1)])

    if rpc is None:
        state["status"] = "failed"
        state["last_error"] = last_error or "wss_failed_without_http_fallback"
        return state

    state["fallback_used"] = True
    try:
        await ingestor.backfill()
        state["processed"] = ingestor.processed
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
