from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import DashboardSummaryResponse
from app.services.analytics import get_dashboard_summary

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/summary", response_model=DashboardSummaryResponse)
def dashboard_summary(
    vendor_id: Optional[int] = Query(None, description="Filter by vendor ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db)
):
    """Returns top KPI cards, trends, category spend, and data quality alerts."""
    return get_dashboard_summary(db, vendor_id=vendor_id, category=category)
