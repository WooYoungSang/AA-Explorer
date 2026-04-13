from fastapi import APIRouter, Request

from app.schemas import PaymastersResponse
from app.services.queries import get_paymaster_distribution

router = APIRouter()


@router.get("", response_model=PaymastersResponse)
async def list_paymasters(request: Request) -> PaymastersResponse:
    items, total_sponsored = await get_paymaster_distribution(request.app.state.db_path)
    return PaymastersResponse(items=items, total_sponsored=total_sponsored)
