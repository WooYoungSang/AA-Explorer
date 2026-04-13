from fastapi import APIRouter, Request

from app.schemas import SmartAccountsResponse
from app.services.queries import get_smart_account_distribution

router = APIRouter()


@router.get("", response_model=SmartAccountsResponse)
async def list_smart_accounts(request: Request) -> SmartAccountsResponse:
    items, total_accounts = await get_smart_account_distribution(request.app.state.db_path)
    return SmartAccountsResponse(items=items, total_accounts=total_accounts)
