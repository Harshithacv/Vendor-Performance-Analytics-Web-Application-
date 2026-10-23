from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Body, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import VendorSummaryMetrics
from app.schemas import VendorComparisonResponse, VendorComparisonRequest
from app.services.analytics import get_vendor_comparison

router = APIRouter(prefix="/api/analytics", tags=["Performance & Comparison"])

@router.get("/vendor-performance")
def vendor_performance(
    top_n: int = Query(10, ge=3, le=50),
    db: Session = Depends(get_db)
):
    """Returns top ranked vendors by Composite Vendor Performance Index (CVPI)."""
    top_vendors = db.query(VendorSummaryMetrics).order_by(VendorSummaryMetrics.vendor_rank.asc()).limit(top_n).all()
    return {
        "scoring_methodology": {
            "name": "Composite Vendor Performance Index (CVPI)",
            "scale": "0 - 100",
            "weights": {
                "spend_scale_volume": "20%",
                "profit_margin": "25%",
                "stock_turnover": "25%",
                "delivery_speed_and_sla": "20%",
                "freight_efficiency": "10%"
            }
        },
        "top_ranked_vendors": [
            {
                "rank": v.vendor_rank,
                "vendor_id": v.vendor_id,
                "vendor_name": v.vendor_name,
                "vendor_score": float(v.vendor_score),
                "profit_margin": float(v.profit_margin),
                "stock_turnover": float(v.stock_turnover),
                "avg_delivery_days": float(v.avg_delivery_days),
                "on_time_delivery_rate": float(v.on_time_delivery_rate),
                "spend": float(v.total_purchase_dollars)
            }
            for v in top_vendors
        ]
    }

@router.post("/vendor-comparison", response_model=VendorComparisonResponse)
def compare_vendors(
    payload: VendorComparisonRequest,
    db: Session = Depends(get_db)
):
    """Compares 2 to 10 vendors head-to-head across radar dimensions, statistical metrics, and CIs."""
    if len(payload.vendor_ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 vendors must be selected for comparison."
        )
    return get_vendor_comparison(db, vendor_ids=payload.vendor_ids)

@router.get("/vendor-comparison", response_model=VendorComparisonResponse)
def compare_vendors_get(
    vendor_ids: str = Query(..., description="Comma-separated vendor IDs (e.g. 1,2,3)"),
    db: Session = Depends(get_db)
):
    try:
        v_ids = [int(x.strip()) for x in vendor_ids.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="vendor_ids must be comma-separated integers")
    if len(v_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 vendors must be selected for comparison")
    return get_vendor_comparison(db, vendor_ids=v_ids)
