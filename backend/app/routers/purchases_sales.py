from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import PurchasingAnalyticsResponse, SalesAnalyticsResponse
from app.services.analytics import get_purchasing_analytics, get_sales_analytics

router = APIRouter(prefix="/api/analytics", tags=["Purchasing & Sales Analytics"])

@router.get("/purchasing", response_model=PurchasingAnalyticsResponse)
def purchasing_analytics(
    vendor_id: Optional[int] = Query(None, description="Filter by vendor ID"),
    db: Session = Depends(get_db)
):
    """Returns procurement spend, bulk purchasing tiers, Pareto dependency, and spend trends."""
    return get_purchasing_analytics(db, vendor_id=vendor_id)

@router.get("/sales", response_model=SalesAnalyticsResponse)
def sales_analytics(
    vendor_id: Optional[int] = Query(None, description="Filter by vendor ID"),
    db: Session = Depends(get_db)
):
    """Returns downstream revenue, gross profits, sales vs purchases comparison, and pricing opportunities."""
    return get_sales_analytics(db, vendor_id=vendor_id)
