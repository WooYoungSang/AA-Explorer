from fastapi import APIRouter, HTTPException, Query, Request

from app.schemas import UserOp, UserOpsResponse
from app.services.queries import get_userop_by_hash, get_userops

router = APIRouter()


@router.get("", response_model=UserOpsResponse)
async def list_userops(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> UserOpsResponse:
    items, total = await get_userops(request.app.state.db_path, page=page, per_page=per_page)
    return UserOpsResponse(items=items, total=total, page=page)


@router.get("/{user_op_hash}", response_model=UserOp)
async def get_userop(request: Request, user_op_hash: str) -> UserOp:
    item = await get_userop_by_hash(user_op_hash, request.app.state.db_path)
    if item is None:
        raise HTTPException(status_code=404, detail="UserOp not found")
    return UserOp.model_validate(item)
