from fastapi import APIRouter, Query

router = APIRouter()


@router.get("")
async def list_userops(page: int = Query(1, ge=1)) -> dict[str, object]:
    return {"items": [], "total": 0, "page": page}
