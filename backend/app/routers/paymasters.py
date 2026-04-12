from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_paymasters() -> dict[str, object]:
    return {"items": [], "total_sponsored": 0}
