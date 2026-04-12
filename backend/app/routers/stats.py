from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def get_stats() -> dict[str, object]:
    return {"daily": [], "total_ops": 0, "active_wallets": 0}
