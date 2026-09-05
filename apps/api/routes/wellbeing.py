from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from services.wellbeing import WellbeingAnalyticsService

router = APIRouter(prefix="/api/v1/wellbeing", tags=["Digital Wellbeing"])


@router.get("")
def get_wellbeing_dashboard(db: Session = Depends(get_db)):
    """
    Returns complete Digital Wellbeing analytics, Focus scores, Deep Work detection,
    Context switches, Anomaly events, and Recommendations computed from database events.
    """
    return WellbeingAnalyticsService.get_full_wellbeing_metrics(db)
