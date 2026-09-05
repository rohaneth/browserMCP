from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from services.twin import DigitalTwinService

router = APIRouter(prefix="/api/v1/twin", tags=["Digital Twin"])


@router.get("")
def get_digital_twin_model(db: Session = Depends(get_db)):
    """
    Returns the evidence-backed behavioral Digital Twin model generated
    from real browser activity, semantic clustering, memory records, and investigations.
    """
    return DigitalTwinService.get_digital_twin_model(db)
