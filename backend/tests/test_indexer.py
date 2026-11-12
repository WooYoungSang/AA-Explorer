from __future__ import annotations

import json
import sqlite3

import pytest
from app.config import ENTRYPOINT_V07
from app.services import indexer
from app.services.decoder import ACCOUNT_DEPLOYED_TOPIC0, USER_OPERATION_EVENT_TOPIC0
from app.services.indexer import start_indexer


class FakeWebSocket:
    def __init__(self, messages):
        self.messages = list(messages)
        self.sent = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def send(self, payload: str) -> None:
        self.sent.append(payload)

    async def recv(self) -> str:
        if not self.messages:
            raise RuntimeError("no more websocket messages")
        return self.messages.pop(0)


class FailingConnector:
    def __init__(self):
        self.calls = 0

    def __call__(self, url: str):
        self.calls += 1
        return self

    async def __aenter__(self):
        raise OSError("wss unavailable")

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeRpc:
    """Fake JSON-RPC node: records calls, serves logs and block timestamps."""

    def __init__(self, *, head=1000, logs=(), max_span=None, timestamps=None):
        self.head = head
        self.logs = list(logs)
        self.max_span = max_span
        self.timestamps = timestamps or {}
        self.calls: list[tuple[str, list]] = []

    async def __call__(self, method, params):
        self.calls.append((method, params))
        if method == "eth_blockNumber":
            return hex(self.head)
        if method == "eth_getBlockByNumber":
            number = int(params[0], 16)
            return {
                "number": params[0],
                "timestamp": hex(self.timestamps.get(number, 1_710_000_000 + number)),
            }
        if method == "eth_getLogs":
            start, end = int(params[0]["fromBlock"], 16), int(params[0]["toBlock"], 16)
            if self.max_span is not None and end - start + 1 > self.max_span:
                raise RuntimeError("block range too large")
            return [log for log in self.logs if start <= int(log["blockNumber"], 16) <= end]
        raise AssertionError(method)

    def get_logs_ranges(self):
        return [
            (int(p[0]["fromBlock"], 16), int(p[0]["toBlock"], 16))
            for m, p in self.calls
            if m == "eth_getLogs"
        ]


def _subscription(event) -> str:
    return json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "eth_subscription",
            "params": {"subscription": "s", "result": event},
        }
    )


def _sub_ack() -> str:
    return '{"jsonrpc":"2.0","id":1,"result":"sub-1"}'


def _rows(
    db_path, sql="SELECT user_op_hash, timestamp, factory, nonce FROM user_ops ORDER BY log_index"
):
    with sqlite3.connect(db_path) as db:
        try:
            return db.execute(sql).fetchall()
        except sqlite3.OperationalError:  # table never created: nothing was stored
            return []


def _last_block(db_path):
    with sqlite3.connect(db_path) as db:
        row = db.execute("SELECT last_block FROM indexer_state").fetchone()
    return None if row is None else row[0]


def test_entrypoint_v07_address() -> None:
    assert ENTRYPOINT_V07.startswith("0x")
    assert len(ENTRYPOINT_V07) == 42


@pytest.mark.asyncio
async def test_indexer_processes_websocket_event(build_user_operation_event_log, tmp_path) -> None:
    db_path = str(tmp_path / "aa_explorer.db")
    rpc = FakeRpc(head=123)
    websocket = FakeWebSocket([_sub_ack(), _subscription(build_user_operation_event_log())])

    state = await start_indexer(
        "wss://example",
        db_path=db_path,
        websocket_factory=lambda _url: websocket,
        rpc_call=rpc,
        stop_after_events=1,
    )

    assert state == {
        "status": "completed",
        "rpc_wss": "wss://example",
        "rpc_https": None,
        "processed": 1,
        "retries": 0,
        "fallback_used": False,
    }
    assert websocket.sent
    assert _rows(db_path)[0][:2] == ("0x" + "11" * 32, 1_710_000_000 + 123)


@pytest.mark.asyncio
async def test_indexer_falls_back_to_http_after_retries(tmp_path) -> None:
    db_path = str(tmp_path / "aa_explorer.db")
    connector = FailingConnector()
    slept = []

    async def fake_sleep(seconds: float) -> None:
        slept.append(seconds)

    rpc = FakeRpc(head=1000)
    state = await start_indexer(
        "wss://example",
        "https://example",
        db_path=db_path,
        websocket_factory=connector,
        rpc_call=rpc,
        sleep=fake_sleep,
    )

    assert state["status"] == "completed"
    assert state["retries"] == 5
    assert state["fallback_used"] is True
    assert connector.calls == 5
    assert slept == [1, 2, 4, 8, 16]


@pytest.mark.asyncio
async def test_real_fixture_ingested_with_factory_and_block_timestamp(
    real_logs, tmp_path, monkeypatch
) -> None:
    db_path = str(tmp_path / "aa_explorer.db")
    block = int(real_logs["block"]["number"], 16)
    timestamp = int(real_logs["block"]["timestamp"], 16)
    rpc = FakeRpc(head=block + 1, logs=real_logs["logs"], timestamps={block: timestamp})
    stored = []

    async def capture(_db_path, record):  # real nonce is 192-bit; storage is another lane's job
        stored.append(record)
        return record

    async def no_aggregate(_db_path):
        return []

    monkeypatch.setattr(indexer, "store_user_op", capture)
    monkeypatch.setattr(indexer, "aggregate_daily_stats", no_aggregate)
    await indexer._save_last_block(db_path, block - 1)

    await start_indexer(
        "wss://example",
        db_path=db_path,
        websocket_factory=lambda _url: FakeWebSocket([_sub_ack()]),
        rpc_call=rpc,
        max_retries=1,
        sleep=_no_sleep,
    )

    assert len(stored) == 1
    record = stored[0]
    assert record["timestamp"] == timestamp
    assert record["factory"] == "0x4e1DCf7AD4e460CfD30791CCC4F9c8a4f820ec67"
    assert record["paymaster"] is None
    assert record["nonce"] >= 2**63 and isinstance(record["nonce"], int)


async def _no_sleep(_seconds: float) -> None:
    return None


@pytest.mark.asyncio
async def test_factory_none_when_no_account_deployed(
    build_user_operation_event_log, tmp_path
) -> None:
    db_path = str(tmp_path / "aa_explorer.db")
    rpc = FakeRpc(head=101, logs=[build_user_operation_event_log(block_number=100)])
    await indexer._save_last_block(db_path, 99)

    await start_indexer(
        "wss://x",
        db_path=db_path,
        websocket_factory=lambda _u: FakeWebSocket([_sub_ack()]),
        rpc_call=rpc,
        max_retries=1,
        sleep=_no_sleep,
    )

    assert _rows(db_path)[0][2] is None


@pytest.mark.asyncio
async def test_two_userops_in_one_tx_each_get_own_factory(
    build_user_operation_event_log, build_account_deployed_log, tmp_path
) -> None:
    db_path = str(tmp_path / "aa_explorer.db")
    a, b = "0x" + "a1" * 32, "0x" + "a2" * 32
    logs = [
        build_account_deployed_log(
            user_op_hash=a, factory="0x" + "f1" * 20, log_index=1, block_number=100
        ),
        build_account_deployed_log(
            user_op_hash=b, factory="0x" + "f2" * 20, log_index=2, block_number=100
        ),
        build_user_operation_event_log(user_op_hash=a, log_index=3, block_number=100),
        build_user_operation_event_log(user_op_hash=b, log_index=4, block_number=100),
    ]
    await indexer._save_last_block(db_path, 99)

    await start_indexer(
        "wss://x",
        db_path=db_path,
        websocket_factory=lambda _u: FakeWebSocket([_sub_ack()]),
        rpc_call=FakeRpc(head=100, logs=logs),
        max_retries=1,
        sleep=_no_sleep,
    )

    assert [row[2].lower() for row in _rows(db_path)] == ["0x" + "f1" * 20, "0x" + "f2" * 20]


@pytest.mark.asyncio
async def test_block_timestamp_fetched_once_per_block(
    build_user_operation_event_log, tmp_path
) -> None:
    db_path = str(tmp_path / "aa_explorer.db")
    logs = [
        build_user_operation_event_log(
            user_op_hash="0x" + f"{i:02x}" * 32, log_index=i, block_number=100
        )
        for i in range(1, 4)
    ] + [
        build_user_operation_event_log(user_op_hash="0x" + "ee" * 32, log_index=1, block_number=101)
    ]
    rpc = FakeRpc(head=101, logs=logs)
    await indexer._save_last_block(db_path, 100)

    await start_indexer(
        "wss://x",
        db_path=db_path,
        websocket_factory=lambda _u: FakeWebSocket([_sub_ack()]),
        rpc_call=rpc,
        max_retries=1,
        sleep=_no_sleep,
    )

    block_calls = [p[0] for m, p in rpc.calls if m == "eth_getBlockByNumber"]
    assert sorted(block_calls) == [hex(100), hex(101)]
    assert len(_rows(db_path)) == 4


@pytest.mark.asyncio
async def test_no_record_stored_with_timestamp_zero(
    build_user_operation_event_log, tmp_path
) -> None:
    db_path = str(tmp_path / "aa_explorer.db")
    rpc = FakeRpc(
        head=100, logs=[build_user_operation_event_log(block_number=100)], timestamps={100: 0}
    )
    await indexer._save_last_block(db_path, 99)

    state = await start_indexer(
        "wss://x",
        "https://x",
        db_path=db_path,
        websocket_factory=lambda _u: FakeWebSocket([_sub_ack()]),
        rpc_call=rpc,
        max_retries=1,
        sleep=_no_sleep,
    )

    assert _rows(db_path) == []
    assert state["status"] == "failed"


@pytest.mark.asyncio
async def test_backfill_from_last_processed_block_on_connect(
    build_user_operation_event_log, tmp_path
) -> None:
    db_path = str(tmp_path / "aa_explorer.db")
    await indexer._save_last_block(db_path, 500)
    rpc = FakeRpc(head=510, logs=[build_user_operation_event_log(block_number=505)])
    websocket = FakeWebSocket(
        [
            _sub_ack(),
            _subscription(
                build_user_operation_event_log(user_op_hash="0x" + "99" * 32, block_number=511)
            ),
        ]
    )

    await start_indexer(
        "wss://x",
        db_path=db_path,
        websocket_factory=lambda _u: websocket,
        rpc_call=rpc,
        stop_after_events=2,
    )

    assert rpc.get_logs_ranges()[0] == (500, 510)
    assert [m for m, _ in rpc.calls][:2] == [
        "eth_blockNumber",
        "eth_getLogs",
    ]  # before any block lookup
    assert {row[0] for row in _rows(db_path)} == {"0x" + "11" * 32, "0x" + "99" * 32}
    assert _last_block(db_path) == 510


@pytest.mark.asyncio
async def test_gap_over_20_blocks_filled(build_user_operation_event_log, tmp_path) -> None:
    db_path = str(tmp_path / "aa_explorer.db")
    await indexer._save_last_block(db_path, 100)
    rpc = FakeRpc(head=300, logs=[build_user_operation_event_log(block_number=150)])

    await start_indexer(
        "wss://x",
        db_path=db_path,
        websocket_factory=lambda _u: FakeWebSocket([_sub_ack()]),
        rpc_call=rpc,
        max_retries=1,
        sleep=_no_sleep,
    )

    assert rpc.get_logs_ranges()[0] == (100, 300)
    assert len(_rows(db_path)) == 1


@pytest.mark.asyncio
async def test_range_halved_when_node_refuses(build_user_operation_event_log, tmp_path) -> None:
    db_path = str(tmp_path / "aa_explorer.db")
    await indexer._save_last_block(db_path, 1000)
    logs = [
        build_user_operation_event_log(
            user_op_hash="0x" + f"{b:02x}" * 32, block_number=b, log_index=1
        )
        for b in (1000, 1700, 3000)
    ]
    rpc = FakeRpc(head=3999, logs=logs, max_span=500)

    await start_indexer(
        "wss://x",
        db_path=db_path,
        websocket_factory=lambda _u: FakeWebSocket([_sub_ack()]),
        rpc_call=rpc,
        max_retries=1,
        sleep=_no_sleep,
    )

    ranges = rpc.get_logs_ranges()
    spans = [end - start + 1 for start, end in ranges]
    assert spans[:4] == [2000, 1000, 500, 500]  # 2000 refused, halved until accepted
    assert ranges[-1][1] == 3999
    assert len(_rows(db_path)) == 3
    assert _last_block(db_path) == 3999


@pytest.mark.asyncio
async def test_first_start_does_not_fetch_history(tmp_path) -> None:
    db_path = str(tmp_path / "aa_explorer.db")
    rpc = FakeRpc(head=777)

    await start_indexer(
        "wss://x",
        db_path=db_path,
        websocket_factory=lambda _u: FakeWebSocket([_sub_ack()]),
        rpc_call=rpc,
        max_retries=1,
        sleep=_no_sleep,
    )

    assert all(start >= 777 for start, _end in rpc.get_logs_ranges())  # nothing before first start
    assert _last_block(db_path) == 777


@pytest.mark.asyncio
async def test_removed_log_deletes_row_and_recomputes_stats(
    build_user_operation_event_log, tmp_path
) -> None:
    db_path = str(tmp_path / "aa_explorer.db")
    keep = build_user_operation_event_log(
        user_op_hash="0x" + "aa" * 32, log_index=1, block_number=100
    )
    drop = build_user_operation_event_log(
        user_op_hash="0x" + "bb" * 32, sender="0x" + "44" * 20, log_index=2, block_number=100
    )
    removed = dict(drop, removed=True)
    websocket = FakeWebSocket(
        [_sub_ack(), _subscription(keep), _subscription(drop), _subscription(removed)]
    )
    rpc = FakeRpc(head=100)

    state = await start_indexer(
        "wss://x",
        db_path=db_path,
        websocket_factory=lambda _u: websocket,
        rpc_call=rpc,
        max_retries=1,
        sleep=_no_sleep,
    )

    assert state["processed"] == 2  # the fake socket then runs dry and the retry budget ends
    assert [row[0] for row in _rows(db_path)] == ["0x" + "aa" * 32]
    stats = _rows(db_path, "SELECT total_ops, unique_senders FROM daily_stats")
    assert stats == [(1, 1)]


@pytest.mark.asyncio
async def test_subscribe_and_getlogs_filters_carry_address_and_both_topics(
    build_user_operation_event_log, tmp_path
) -> None:
    db_path = str(tmp_path / "aa_explorer.db")
    await indexer._save_last_block(db_path, 10)
    rpc = FakeRpc(head=12)
    websocket = FakeWebSocket([_sub_ack()])

    await start_indexer(
        "wss://x",
        db_path=db_path,
        websocket_factory=lambda _u: websocket,
        rpc_call=rpc,
        max_retries=1,
        sleep=_no_sleep,
    )

    subscribe_filter = json.loads(websocket.sent[0])["params"][1]
    getlogs_filter = next(p[0] for m, p in rpc.calls if m == "eth_getLogs")
    for flt in (subscribe_filter, getlogs_filter):
        assert flt["address"] == ENTRYPOINT_V07
        assert flt["topics"] == [[USER_OPERATION_EVENT_TOPIC0, ACCOUNT_DEPLOYED_TOPIC0]]
        assert all(t.startswith("0x") for t in flt["topics"][0])


@pytest.mark.asyncio
async def test_factory_kept_for_every_record_in_a_chunk_over_1000_pairs(
    build_user_operation_event_log, build_account_deployed_log, tmp_path
) -> None:
    db_path = str(tmp_path / "aa_explorer.db")
    factory = "0x" + "f1" * 20
    logs = []
    for i in range(1001):
        user_op_hash = "0x" + f"{i + 1:064x}"
        block = 1000 + i % 500
        logs.append(
            build_account_deployed_log(
                user_op_hash=user_op_hash,
                factory=factory,
                block_number=block,
                log_index=2 * i,
                tx_hash=user_op_hash,
            )
        )
        logs.append(
            build_user_operation_event_log(
                user_op_hash=user_op_hash,
                block_number=block,
                log_index=2 * i + 1,
                tx_hash=user_op_hash,
            )
        )
    await indexer._save_last_block(db_path, 999)
    rpc = FakeRpc(head=1500, logs=logs)

    await start_indexer(
        "wss://x",
        db_path=db_path,
        websocket_factory=lambda _u: FakeWebSocket([_sub_ack()]),
        rpc_call=rpc,
        max_retries=1,
        sleep=_no_sleep,
    )

    assert rpc.get_logs_ranges()[0] == (999, 1500)  # a single chunk
    rows = _rows(db_path)
    assert len(rows) == 1001
    assert [row for row in rows if row[2] is None] == []


@pytest.mark.asyncio
async def test_blocks_between_http_head_and_first_subscription_event_are_fetched(
    build_user_operation_event_log, tmp_path
) -> None:
    db_path = str(tmp_path / "aa_explorer.db")
    await indexer._save_last_block(db_path, 95)
    missed = build_user_operation_event_log(user_op_hash="0x" + "b1" * 32, block_number=101)
    live = build_user_operation_event_log(user_op_hash="0x" + "b2" * 32, block_number=102)
    rpc = FakeRpc(head=100, logs=[missed])  # HTTP node is one block behind the WSS node
    websocket = FakeWebSocket([_sub_ack(), _subscription(live)])

    await start_indexer(
        "wss://x",
        db_path=db_path,
        websocket_factory=lambda _u: websocket,
        rpc_call=rpc,
        stop_after_events=2,
    )

    assert {row[0] for row in _rows(db_path)} == {"0x" + "b1" * 32, "0x" + "b2" * 32}
    assert rpc.get_logs_ranges() == [(95, 100), (101, 101)]
    assert _last_block(db_path) == 101
