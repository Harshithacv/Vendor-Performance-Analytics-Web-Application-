from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Vendor, VendorSummaryMetrics, User
from app.schemas import VendorListResponse, VendorDetailResponse, VendorCreate, VendorResponse
from app.auth import require_admin
from app.services.analytics import get_vendor_list, get_vendor_detail

router = APIRouter(prefix="/api/vendors", tags=["Vendors"])

@router.get("", response_model=VendorListResponse)
def list_vendors(
    search: Optional[str] = Query(None, description="Search by name or number"),
    category: Optional[str] = Query(None, description="Filter by category"),
    sort_by: str = Query("vendor_score", description="Sort column (vendor_score, total_purchase_dollars, etc.)"),
    sort_dir: str = Query("desc", description="Sort direction (asc/desc)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Returns a paginated list of vendors with performance scores, spend, and delivery metrics."""
    return get_vendor_list(
        db, search=search, category=category, sort_by=sort_by, 
        sort_dir=sort_dir, page=page, page_size=page_size
    )

@router.post("", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
def create_vendor(
    vendor_in: VendorCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Creates a new vendor in MySQL. Available to authenticated application users.
    """
    # Check if vendor number already exists
    existing = db.query(Vendor).filter(Vendor.vendor_number == vendor_in.vendor_number).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vendor with number {vendor_in.vendor_number} already exists in the catalog."
        )

    # Insert new vendor
    new_vendor = Vendor(
        vendor_number=vendor_in.vendor_number,
        vendor_name=vendor_in.vendor_name.strip(),
        category=vendor_in.category.strip() if vendor_in.category else "Beverage & Spirits"
    )
    db.add(new_vendor)
    db.commit()
    db.refresh(new_vendor)

    # Initialize a baseline VendorSummaryMetrics entry
    total_existing = db.query(VendorSummaryMetrics).count() or 0
    new_summary = VendorSummaryMetrics(
        vendor_id=new_vendor.vendor_id,
        vendor_number=new_vendor.vendor_number,
        vendor_name=new_vendor.vendor_name,
        total_purchase_dollars=0.0,
        total_purchase_quantity=0,
        total_sales_dollars=0.0,
        total_sales_quantity=0,
        gross_profit=0.0,
        profit_margin=0.0,
        stock_turnover=0.0,
        sales_to_purchase_ratio=0.0,
        freight_cost=0.0,
        freight_percentage=0.0,
        total_orders=0,
        avg_delivery_days=0.0,
        on_time_delivery_rate=0.0,
        defect_rate=0.0,
        vendor_score=0.0,
        vendor_rank=total_existing + 1,
        ci_lower=0.0,
        ci_upper=0.0
    )
    db.add(new_summary)
    db.commit()

    total_vendors_now = db.query(Vendor).count()

    return {
        "vendor_id": new_vendor.vendor_id,
        "vendor_number": new_vendor.vendor_number,
        "vendor_name": new_vendor.vendor_name,
        "category": new_vendor.category,
        "created_at": new_vendor.created_at,
        "message": f"Vendor '{new_vendor.vendor_name}' successfully added.",
        "total_vendors_count": total_vendors_now
    }

@router.get("/{vendor_id}", response_model=VendorDetailResponse)
def vendor_detail(vendor_id: int, db: Session = Depends(get_db)):
    """Returns detailed performance breakdown, PO history, and brand contributions for a single vendor."""
    detail = get_vendor_detail(db, vendor_id=vendor_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Vendor with ID {vendor_id} not found"
        )
    return detail
