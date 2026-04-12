import pytest
from app.config import ENTRYPOINT_V07
from app.services.decoder import decode_user_op
from app.services.indexer import start_indexer


def test_entrypoint_v07_address() -> None:
    assert ENTRYPOINT_V07.startswith("0x")
    assert len(ENTRYPOINT_V07) == 42


@pytest.mark.asyncio
async def test_decoder_handles_empty_input() -> None:
    assert await decode_user_op(b"") is None


@pytest.mark.asyncio
async def test_indexer_returns_placeholder_state() -> None:
    assert await start_indexer("wss://example") == {
        "status": "not-started",
        "rpc_wss": "wss://example",
    }
