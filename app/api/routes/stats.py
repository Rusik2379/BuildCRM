from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.services.stats_service import StatsService

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/dashboard")
def dashboard_stats(db: Session = Depends(get_db_session)):
    return StatsService.get_dashboard_stats(db)
