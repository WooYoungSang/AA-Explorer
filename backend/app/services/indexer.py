async def start_indexer(rpc_wss: str) -> dict[str, str]:
    return {"status": "not-started", "rpc_wss": rpc_wss}
