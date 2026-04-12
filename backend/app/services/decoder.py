async def decode_user_op(raw: bytes):
    if not raw:
        return None
    return {"raw_length": len(raw)}
