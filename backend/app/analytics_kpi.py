"""
Procurement Analytics & Vendor KPI Engine
Calculates:
- On-Time Delivery Rate (OTDR %)
- Quality Rating Average (QRA / 5.0)
- Order Fulfillment Rate (OFR %)
- Composite Vendor Performance Index (VPI) & Status Classification
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np


def compute_otdr(df: pd.DataFrame) -> float:
    """
    Computes On-Time Delivery Rate (OTDR %):
    Percentage of delivered orders that arrived on or before expected delivery date.
    """
    if df.empty:
        return 0.0

    # Filter for delivered orders where delivery variance is known
    delivered = df[df["actual_delivery"].notna() | (df.get("order_status") == "Delivered")].copy()
    if delivered.empty:
        return 0.0

    if "delivery_delay_days" in delivered.columns:
        on_time = (delivered["delivery_delay_days"] <= 0).sum()
    else:
        # Calculate from date columns
        act = pd.to_datetime(delivered["actual_delivery"], errors="coerce")
        exp = pd.to_datetime(delivered["expected_delivery"], errors="coerce")
        on_time = ((act - exp).dt.days <= 0).sum()

    total_delivered = len(delivered)
    return round((on_time / total_delivered) * 100.0, 2) if total_delivered > 0 else 0.0


def compute_qra(df: pd.DataFrame) -> float:
    """
    Computes Quality Rating Average (QRA):
    Arithmetic mean of dock receiving quality scores (scale 1.0 to 5.0).
    """
    if df.empty or "quality_score" not in df.columns:
        return 0.0

    valid_scores = pd.to_numeric(df["quality_score"], errors="coerce").dropna()
    if valid_scores.empty:
        return 0.0

    return round(float(valid_scores.mean()), 2)


def compute_fulfillment_rate(df: pd.DataFrame) -> float:
    """
    Computes Order Fulfillment Rate (OFR %):
    (Total Quantity Received / Total Quantity Ordered) * 100
    """
    if df.empty or "quantity_ordered" not in df.columns:
        return 0.0

    ordered = pd.to_numeric(df["quantity_ordered"], errors="coerce").fillna(0).sum()
    received = pd.to_numeric(df.get("quantity_received", 0), errors="coerce").fillna(0).sum()

    if ordered <= 0:
        return 0.0

    return round(float((received / ordered) * 100.0), 2)


def rank_vendor_performance(otdr: float, qra: float, fulfillment: float) -> Dict[str, Any]:
    """
    Computes composite Vendor Performance Index (VPI out of 100) and ranking status:
    Weights:
      - OTDR: 40%
      - Quality: 35% (normalized from 5.0 scale to 100)
      - Fulfillment Rate: 25%
    """
    normalized_quality = (qra / 5.0) * 100.0
    vpi = round((0.40 * otdr) + (0.35 * normalized_quality) + (0.25 * fulfillment), 2)

    # Classification logic
    if otdr >= 90.0 and qra >= 4.2 and fulfillment >= 95.0:
        status = "Top Performer"
    elif otdr < 75.0 or qra < 3.5 or fulfillment < 85.0:
        status = "Underperforming"
    else:
        status = "At Risk"

    return {
        "vpi_score": vpi,
        "performance_status": status,
        "is_sla_compliant": otdr >= 90.0,
    }


def compute_vendor_scorecards(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Generates detailed vendor scorecards including individual OTDR, QRA,
    fulfillment, spend YTD, and dynamic ranking.
    """
    if df.empty or "vendor_id" not in df.columns:
        return []

    scorecards = []
    for vendor_id, group in df.groupby("vendor_id"):
        vendor_name = group["vendor_name"].iloc[0] if "vendor_name" in group.columns else vendor_id
        category = group["category"].iloc[0] if "category" in group.columns else "General"

        total_orders = len(group)
        total_spend = round(float(pd.to_numeric(group.get("total_spend", 0), errors="coerce").fillna(0).sum()), 2)

        vendor_otdr = compute_otdr(group)
        vendor_qra = compute_qra(group)
        vendor_fulfillment = compute_fulfillment_rate(group)

        # Average delivery variance for delivered orders
        delivered = group[group["actual_delivery"].notna()].copy()
        if not delivered.empty and "delivery_delay_days" in delivered.columns:
            avg_delay = round(float(delivered["delivery_delay_days"].mean()), 1)
        else:
            avg_delay = 0.0

        ranking = rank_vendor_performance(vendor_otdr, vendor_qra, vendor_fulfillment)

        scorecards.append({
            "vendor_id": str(vendor_id),
            "vendor_name": str(vendor_name),
            "category": str(category),
            "total_orders": total_orders,
            "total_spend": total_spend,
            "otdr": vendor_otdr,
            "quality_rating_avg": vendor_qra,
            "fulfillment_rate": vendor_fulfillment,
            "avg_delay_days": avg_delay,
            "vpi_score": ranking["vpi_score"],
            "status": ranking["performance_status"],
            "is_sla_compliant": ranking["is_sla_compliant"],
        })

    # Sort descending by composite VPI score
    scorecards.sort(key=lambda x: x["vpi_score"], reverse=True)

    # Assign rank order
    for idx, card in enumerate(scorecards, start=1):
        card["rank"] = idx

    return scorecards


def compute_executive_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes overarching executive dashboard KPIs across the entire procurement portfolio.
    """
    if df.empty:
        return {
            "total_spend": 0.0,
            "total_orders": 0,
            "active_vendors": 0,
            "otdr": 0.0,
            "qra": 0.0,
            "fulfillment_rate": 0.0,
            "delayed_orders_count": 0,
            "in_transit_count": 0,
            "category_spend_breakdown": {},
        }

    total_spend = round(float(pd.to_numeric(df.get("total_spend", 0), errors="coerce").fillna(0).sum()), 2)
    total_orders = len(df)
    active_vendors = int(df["vendor_id"].nunique()) if "vendor_id" in df.columns else 0

    global_otdr = compute_otdr(df)
    global_qra = compute_qra(df)
    global_fulfillment = compute_fulfillment_rate(df)

    # Delayed orders identification
    if "order_status" in df.columns:
        delayed_count = int((df["order_status"] == "Delayed").sum())
        in_transit_count = int((df["order_status"] == "In Transit").sum())
    else:
        delayed_mask = (df["actual_delivery"].isna()) & (pd.to_datetime(df["expected_delivery"], errors="coerce") < pd.Timestamp.now())
        delayed_count = int(delayed_mask.sum())
        in_transit_count = int(df["actual_delivery"].isna().sum()) - delayed_count

    # Category spend breakdown
    category_spend = {}
    if "category" in df.columns and "total_spend" in df.columns:
        cat_group = df.groupby("category")["total_spend"].sum().round(2).to_dict()
        category_spend = {str(k): float(v) for k, v in cat_group.items()}

    return {
        "total_spend": total_spend,
        "total_orders": total_orders,
        "active_vendors": active_vendors,
        "otdr": global_otdr,
        "qra": global_qra,
        "fulfillment_rate": global_fulfillment,
        "delayed_orders_count": delayed_count,
        "in_transit_count": max(0, in_transit_count),
        "category_spend_breakdown": category_spend,
    }
