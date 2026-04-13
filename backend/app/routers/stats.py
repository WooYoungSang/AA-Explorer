from fastapi import APIRouter, Request

from app.schemas import StatsResponse
from app.services.queries import get_stats

router = APIRouter()


@router.get("", response_model=StatsResponse)
async def stats_summary(request: Request) -> StatsResponse:
    stats = await get_stats(request.app.state.db_path)
    return StatsResponse.model_validate(stats)
