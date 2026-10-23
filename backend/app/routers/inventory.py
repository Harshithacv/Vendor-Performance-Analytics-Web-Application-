from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import InventoryAnalyticsResponse
from app.services.analytics import get_inventory_analytics

router = APIRouter(prefix="/api/analytics", tags=["Inventory Analytics"])

@router.get("/inventory", response_model=InventoryAnalyticsResponse)
def inventory_analytics(
    store: Optional[int] = Query(None, description="Filter by store number"),
    db: Session = Depends(get_db)
):
    """Returns beginning vs ending stock, capital locked in unsold inventory, and turnover rates."""
    return get_inventory_analytics(db, store=store)
