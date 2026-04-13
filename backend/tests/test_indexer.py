from __future__ import annotations

import pytest
from app.config import ENTRYPOINT_V07
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


def test_entrypoint_v07_address() -> None:
    assert ENTRYPOINT_V07.startswith("0x")
    assert len(ENTRYPOINT_V07) == 42


@pytest.mark.asyncio
async def test_indexer_processes_websocket_event(build_user_operation_event_log, tmp_path) -> None:
    event = build_user_operation_event_log()
    websocket = FakeWebSocket(
        [
            '{"jsonrpc":"2.0","id":1,"result":"sub-1"}',
            '{"jsonrpc":"2.0","method":"eth_subscription","params":{"subscription":"sub-1","result":'
            + __import__("json").dumps(event)
            + "}}",
        ]
    )

    state = await start_indexer(
        "wss://example",
        db_path=str(tmp_path / "aa_explorer.db"),
        websocket_factory=lambda _url: websocket,
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


@pytest.mark.asyncio
async def test_indexer_falls_back_to_http_after_retries(
    build_user_operation_event_log,
    tmp_path,
) -> None:
    connector = FailingConnector()
    slept = []

    async def fake_sleep(seconds: float) -> None:
        slept.append(seconds)

    async def fake_http_get_logs(_rpc_https: str):
        return [build_user_operation_event_log(user_op_hash="0x" + "77" * 32)]

    state = await start_indexer(
        "wss://example",
        "https://example",
        db_path=str(tmp_path / "aa_explorer.db"),
        websocket_factory=connector,
        http_get_logs=fake_http_get_logs,
        sleep=fake_sleep,
    )

    assert state["status"] == "completed"
    assert state["processed"] == 1
    assert state["retries"] == 5
    assert state["fallback_used"] is True
    assert connector.calls == 5
    assert slept == [1, 2, 4, 8, 16]
