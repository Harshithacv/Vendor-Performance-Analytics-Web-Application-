from typing import List, Optional, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field

# ----------------- AUTH SCHEMAS -----------------
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    user_id: int
    name: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ----------------- VENDOR SCHEMAS -----------------
class VendorCreate(BaseModel):
    vendor_number: int = Field(..., gt=0, description="Unique vendor identification number")
    vendor_name: str = Field(..., min_length=2, max_length=255, description="Official vendor name")
    category: Optional[str] = Field("Beverage & Spirits", max_length=100, description="Vendor industry category")

class VendorResponse(BaseModel):
    vendor_id: int
    vendor_number: int
    vendor_name: str
    category: str
    created_at: datetime
    message: Optional[str] = None
    total_vendors_count: Optional[int] = None

    class Config:
        from_attributes = True

class VendorSummaryItem(BaseModel):
    vendor_id: int
    vendor_number: int
    vendor_name: str
    category: str
    total_purchase_dollars: float
    total_sales_dollars: float
    gross_profit: float
    profit_margin: float
    stock_turnover: float
    sales_to_purchase_ratio: float
    freight_cost: float
    freight_percentage: float
    total_orders: int
    avg_delivery_days: float
    on_time_delivery_rate: float
    defect_rate: float
    vendor_score: float
    vendor_rank: int

    class Config:
        from_attributes = True

class VendorListResponse(BaseModel):
    total_count: int
    page: int
    page_size: int
    vendors: List[VendorSummaryItem]

class VendorDetailResponse(BaseModel):
    vendor_id: int
    vendor_number: int
    vendor_name: str
    category: str
    metrics: VendorSummaryItem
    purchase_history: List[Dict[str, Any]]
    monthly_trends: List[Dict[str, Any]]
    top_brands: List[Dict[str, Any]]


# ----------------- DASHBOARD SCHEMAS -----------------
class KPICardData(BaseModel):
    total_vendors: int
    total_procurement_spend: float
    total_sales_revenue: float
    average_delivery_days: float
    on_time_delivery_rate: float
    average_profit_margin: float
    total_freight_spend: float
    total_purchase_orders: int

class DashboardSummaryResponse(BaseModel):
    kpis: KPICardData
    top_vendors_by_spend: List[Dict[str, Any]]
    top_vendors_by_sales: List[Dict[str, Any]]
    spend_by_category: List[Dict[str, Any]]
    monthly_procurement_trend: List[Dict[str, Any]]
    inventory_snapshot_summary: Dict[str, Any]
    recent_purchase_orders: List[Dict[str, Any]]
    data_quality_notices: List[Dict[str, Any]]


# ----------------- PURCHASE & SALES SCHEMAS -----------------
class PurchasingAnalyticsResponse(BaseModel):
    total_spend: float
    total_orders: int
    total_quantity: int
    avg_order_value: float
    avg_unit_price: float
    spend_by_vendor: List[Dict[str, Any]]
    monthly_spend_trend: List[Dict[str, Any]]
    bulk_purchasing_tiers: List[Dict[str, Any]]
    pareto_procurement: List[Dict[str, Any]]
    recent_transactions: List[Dict[str, Any]]

class SalesAnalyticsResponse(BaseModel):
    total_sales_dollars: float
    total_sales_quantity: float
    gross_profit: float
    avg_profit_margin: float
    monthly_sales_trend: List[Dict[str, Any]]
    top_selling_brands: List[Dict[str, Any]]
    sales_vs_purchases: List[Dict[str, Any]]
    pricing_adjustment_opportunities: List[Dict[str, Any]]


# ----------------- INVENTORY SCHEMAS -----------------
class InventoryAnalyticsResponse(BaseModel):
    begin_inventory_value: float
    begin_inventory_qty: int
    end_inventory_value: float
    end_inventory_qty: int
    net_inventory_change_value: float
    capital_locked_in_unsold_stock: float
    top_excess_inventory_vendors: List[Dict[str, Any]]
    store_inventory_distribution: List[Dict[str, Any]]
    inventory_turnover_by_vendor: List[Dict[str, Any]]
    recent_inventory_records: List[Dict[str, Any]]
    data_availability_notice: Optional[str] = None


# ----------------- COMPARISON SCHEMAS -----------------
class VendorComparisonRequest(BaseModel):
    vendor_ids: List[int] = Field(..., min_length=2, max_length=10)

class VendorComparisonResponse(BaseModel):
    selected_vendors: List[VendorSummaryItem]
    radar_comparison: List[Dict[str, Any]]
    head_to_head_table: List[Dict[str, Any]]
    confidence_intervals: List[Dict[str, Any]]
    analytical_insights: List[str]


# ----------------- UPLOAD & VALIDATION SCHEMAS -----------------
class UploadPreviewResponse(BaseModel):
    upload_id: Optional[int] = None
    file_name: str
    detected_type: str
    total_rows: int
    total_columns: int
    columns: List[str]
    missing_values: Dict[str, int]
    duplicate_rows_detected: int
    validation_status: str  # "VALID", "WARNING", "INVALID"
    validation_messages: List[str]
    preview_rows: List[Dict[str, Any]]
    cleaning_actions_summary: List[str]

class UploadConfirmRequest(BaseModel):
    file_path: str
    detected_type: str
    clean_duplicates: bool = True
    fill_missing_values: bool = True

class UploadBatchResponse(BaseModel):
    upload_id: int
    file_name: str
    file_type: str
    row_count: int
    status: str
    uploaded_at: datetime

    class Config:
        from_attributes = True
