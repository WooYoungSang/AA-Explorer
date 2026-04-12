from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_smart_accounts() -> dict[str, object]:
    return {"items": [], "total_accounts": 0}
