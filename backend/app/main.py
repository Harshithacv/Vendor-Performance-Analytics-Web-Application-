"""
FastAPI Enterprise Procurement Analytics Backend Service
Provides CORS-enabled REST API endpoints for:
- /api/kpis
- /api/vendors
- /api/purchases
- /api/inventory
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np

# Import internal KPI computation module
try:
    from backend.app.analytics_kpi import (
        compute_executive_kpis,
        compute_vendor_scorecards,
        compute_otdr,
        compute_qra,
        compute_fulfillment_rate,
        rank_vendor_performance,
    )
except ImportError:
    from analytics_kpi import (
        compute_executive_kpis,
        compute_vendor_scorecards,
        compute_otdr,
        compute_qra,
        compute_fulfillment_rate,
        rank_vendor_performance,
    )

app = FastAPI(
    title="Vendor Performance Analytics API",
    description="Enterprise REST API for procurement tracking, vendor scorecards, and inventory movement",
    version="1.0.0",
)

# Enable CORS for all frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------------------------------
# In-Memory Data Store & Dataset Loader
# ----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_CSV_PATH = BASE_DIR / "data" / "vendor_data.csv"
CLEANED_CSV_PATH = BASE_DIR / "data" / "cleaned_vendor_data.csv"


def load_dataset() -> pd.DataFrame:
    """Loads cleaned data if available; otherwise loads raw data and performs in-memory cleaning."""
    if CLEANED_CSV_PATH.exists():
        df = pd.read_csv(CLEANED_CSV_PATH)
    elif RAW_CSV_PATH.exists():
        df = pd.read_csv(RAW_CSV_PATH)
        # Apply standard cleaning
        df["quantity_ordered"] = pd.to_numeric(df["quantity_ordered"], errors="coerce").fillna(0).astype(int)
        df["quantity_received"] = pd.to_numeric(df.get("quantity_received"), errors="coerce")
        df.loc[df["actual_delivery"].notna() & df["quantity_received"].isna(), "quantity_received"] = df["quantity_ordered"]
        df["quantity_received"] = df["quantity_received"].fillna(0).astype(int)
        df["unit_cost"] = pd.to_numeric(df["unit_cost"], errors="coerce").fillna(0.0).round(2)
        df["total_spend"] = (df["quantity_ordered"] * df["unit_cost"]).round(2)
    else:
        # Fallback dummy frame if file missing
        df = pd.DataFrame()

    return df


# Cache dataset in memory
CURRENT_DF = load_dataset()


# ----------------------------------------------------------------------------
# Pydantic Request Models
# ----------------------------------------------------------------------------
class PurchaseOrderCreate(BaseModel):
    vendor_id: str = Field(..., example="VND-001")
    vendor_name: str = Field(..., example="Apex Metallurgy Ltd")
    category: str = Field(..., example="Raw Materials")
    purchase_id: Optional[str] = None
    expected_delivery: str = Field(..., example="2024-11-15")
    quantity_ordered: int = Field(..., gt=0, example=5000)
    unit_cost: float = Field(..., gt=0, example=25.0)
    destination_warehouse: Optional[str] = "Central DC - Chicago"
    stock_on_hand: Optional[int] = 4000
    reorder_level: Optional[int] = 2000


# ----------------------------------------------------------------------------
# REST Endpoints
# ----------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "service": "Vendor Performance Analytics API",
        "status": "online",
        "records_loaded": len(CURRENT_DF),
        "endpoints": [
            "/api/kpis",
            "/api/vendors",
            "/api/purchases",
            "/api/inventory",
            "/docs",
        ],
    }


@app.get("/api/kpis")
def get_executive_kpis(
    category: Optional[str] = Query(None, description="Filter by category (e.g. Raw Materials, Electronics)")
):
    """
    Returns executive KPI scorecards:
    - Total spend
    - Active vendors count
    - On-Time Delivery Rate (OTDR %)
    - Quality Rating Average (/5.0)
    - Order Fulfillment Rate (%)
    - Delayed & in-transit counts
    - Spend breakdown by category
    """
    df = CURRENT_DF.copy()
    if category and category != "All":
        df = df[df["category"].str.lower() == category.lower()]

    if df.empty:
        return {"message": "No data found for specified filters", "data": {}}

    kpi_data = compute_executive_kpis(df)
    return {
        "status": "success",
        "category_scope": category or "All",
        "kpis": kpi_data,
    }


@app.get("/api/vendors")
def get_vendors(
    category: Optional[str] = Query(None, description="Filter by commodity category"),
    status: Optional[str] = Query(None, description="Filter by status (Top Performer, At Risk, Underperforming)"),
    sort_by: Optional[str] = Query("vpi_score", description="Sort by metric (vpi_score, otdr, quality_rating_avg, total_spend)"),
    ascending: bool = Query(False, description="Sort order"),
):
    """
    Returns complete vendor directory with calculated KPIs, VPI index, and performance status.
    """
    df = CURRENT_DF.copy()
    if category and category != "All":
        df = df[df["category"].str.lower() == category.lower()]

    scorecards = compute_vendor_scorecards(df)

    if status and status != "All":
        scorecards = [v for v in scorecards if v["status"].lower() == status.lower()]

    # Sort scorecards
    if sort_by in ["vpi_score", "otdr", "quality_rating_avg", "total_spend", "fulfillment_rate"]:
        scorecards.sort(key=lambda x: x.get(sort_by, 0), reverse=not ascending)

    return {
        "status": "success",
        "total_vendors": len(scorecards),
        "vendors": scorecards,
    }


@app.get("/api/vendors/{vendor_id}")
def get_vendor_details(vendor_id: str):
    """
    Returns detailed dossier and order history for a single vendor.
    """
    df = CURRENT_DF[CURRENT_DF["vendor_id"] == vendor_id]
    if df.empty:
        raise HTTPException(status_code=404, detail=f"Vendor '{vendor_id}' not found.")

    scorecards = compute_vendor_scorecards(df)
    vendor_summary = scorecards[0] if scorecards else {}

    orders = df.to_dict(orient="records")
    for o in orders:
        for k, v in o.items():
            if pd.isna(v):
                o[k] = None

    return {
        "status": "success",
        "vendor": vendor_summary,
        "purchase_orders_count": len(orders),
        "purchase_orders": orders,
    }


@app.get("/api/purchases")
def get_purchases(
    status: Optional[str] = Query(None, description="Filter by order status: Delivered, In Transit, Delayed"),
    category: Optional[str] = Query(None, description="Filter by category"),
    vendor_id: Optional[str] = Query(None, description="Filter by vendor ID"),
    limit: int = Query(100, ge=1, le=500),
):
    """
    Returns purchase orders with line quantities, delivery status, variance days, and quality scores.
    """
    df = CURRENT_DF.copy()

    # Determine status if not already column
    if "order_status" not in df.columns:
        conditions = [
            df["actual_delivery"].isna() & (pd.to_datetime(df["expected_delivery"], errors="coerce") < pd.Timestamp.now()),
            df["actual_delivery"].isna(),
            (pd.to_datetime(df["actual_delivery"], errors="coerce") - pd.to_datetime(df["expected_delivery"], errors="coerce")).dt.days <= 0,
            (pd.to_datetime(df["actual_delivery"], errors="coerce") - pd.to_datetime(df["expected_delivery"], errors="coerce")).dt.days > 0,
        ]
        choices = ["Delayed", "In Transit", "Delivered", "Delivered"]
        df["order_status"] = np.select(conditions, choices, default="In Transit")

    if status and status != "All":
        df = df[df["order_status"].str.lower() == status.lower()]

    if category and category != "All":
        df = df[df["category"].str.lower() == category.lower()]

    if vendor_id:
        df = df[df["vendor_id"] == vendor_id]

    records = df.head(limit).to_dict(orient="records")
    for r in records:
        for k, v in r.items():
            if pd.isna(v):
                r[k] = None

    return {
        "status": "success",
        "total_results": len(records),
        "purchases": records,
    }


@app.post("/api/purchases", status_code=status.HTTP_201_CREATED)
def create_purchase_order(po: PurchaseOrderCreate):
    """
    Creates a new purchase order and inserts it into the active in-memory dataset.
    """
    global CURRENT_DF

    today = pd.Timestamp.now().strftime("%Y-%m-%d")
    new_id = po.purchase_id or f"PO-{pd.Timestamp.now().year}-{np.random.randint(1000, 9999)}"
    total_spend = round(po.quantity_ordered * po.unit_cost, 2)

    new_row = {
        "vendor_id": po.vendor_id,
        "vendor_name": po.vendor_name,
        "category": po.category,
        "purchase_id": new_id,
        "purchase_date": today,
        "expected_delivery": po.expected_delivery,
        "actual_delivery": np.nan,
        "quantity_ordered": po.quantity_ordered,
        "quantity_received": 0,
        "unit_cost": po.unit_cost,
        "total_spend": total_spend,
        "quality_score": np.nan,
        "stock_on_hand": po.stock_on_hand,
        "reorder_level": po.reorder_level,
        "order_status": "In Transit",
        "delivery_delay_days": np.nan,
    }

    new_df = pd.DataFrame([new_row])
    CURRENT_DF = pd.concat([CURRENT_DF, new_df], ignore_index=True)

    return {
        "status": "created",
        "purchase_order": {k: (v if pd.notna(v) else None) for k, v in new_row.items()},
    }


@app.get("/api/inventory")
def get_inventory(
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by condition (Optimal, Reorder Warning, Slow-Moving, Critical Shortage)")
):
    """
    Returns inventory stock levels, reorder thresholds, and condition flags.
    """
    df = CURRENT_DF.copy()

    if category and category != "All":
        df = df[df["category"].str.lower() == category.lower()]

    # Deduplicate items by vendor and category to present SKU-level inventory view
    inventory_items = []
    seen_skus = set()

    for idx, row in df.iterrows():
        sku = f"{row['category'][:2].upper()}-{row['vendor_id'][-3:]}"
        if sku in seen_skus:
            continue
        seen_skus.add(sku)

        stock = int(row.get("stock_on_hand", 0))
        reorder = int(row.get("reorder_level", 0))
        unit_cost = float(row.get("unit_cost", 0.0))
        total_val = round(stock * unit_cost, 2)

        # Health status
        if stock < (reorder * 0.5):
            stock_status = "Critical Shortage"
        elif stock <= reorder:
            stock_status = "Reorder Warning"
        elif (reorder > 0) and (stock / reorder) > 2.5:
            stock_status = "Slow-Moving"
        else:
            stock_status = "Optimal"

        if status and status != "All" and stock_status.lower() != status.lower():
            continue

        inventory_items.append({
            "sku": sku,
            "vendor_id": str(row["vendor_id"]),
            "vendor_name": str(row["vendor_name"]),
            "category": str(row["category"]),
            "stock_on_hand": stock,
            "reorder_level": reorder,
            "unit_cost": unit_cost,
            "total_valuation": total_val,
            "stock_status": stock_status,
        })

    return {
        "status": "success",
        "total_items": len(inventory_items),
        "inventory": inventory_items,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
