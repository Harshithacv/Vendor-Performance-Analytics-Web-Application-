#!/usr/bin/env python3
"""
Enterprise Procurement Data Cleaning Pipeline
Standardizes dates, computes delivery delay, imputes missing quantities,
recomputes total spend, and exports cleaned dataset.
"""

import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np


def clean_vendor_data(input_path: str = None, output_path: str = None) -> pd.DataFrame:
    """
    Loads raw procurement CSV data, performs validation, imputation,
    calculates delivery variances, and saves the cleaned dataset.
    """
    base_dir = Path(__file__).resolve().parent.parent
    if input_path is None:
        input_path = base_dir / "data" / "vendor_data.csv"
    else:
        input_path = Path(input_path)

    if output_path is None:
        output_path = base_dir / "data" / "cleaned_vendor_data.csv"
    else:
        output_path = Path(output_path)

    print(f"[*] Loading raw vendor dataset from: {input_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found at {input_path}")

    df = pd.read_csv(input_path)
    initial_rows = len(df)
    print(f"[*] Loaded {initial_rows} rows and {len(df.columns)} columns.")

    # 1. Clean string columns
    str_cols = ["vendor_id", "vendor_name", "category", "purchase_id"]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # 2. Standardize Dates
    date_cols = ["purchase_date", "expected_delivery", "actual_delivery"]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # 3. Impute Missing Quantities
    # If quantity_received is null:
    # - If actual_delivery is populated, order was delivered -> impute with quantity_ordered
    # - If actual_delivery is null (in-transit/pending), quantity_received is 0
    delivered_mask = df["actual_delivery"].notna()
    df["quantity_ordered"] = pd.to_numeric(df["quantity_ordered"], errors="coerce").fillna(0).astype(int)

    # Imputation logic
    df["quantity_received"] = pd.to_numeric(df["quantity_received"], errors="coerce")
    df.loc[delivered_mask & df["quantity_received"].isna(), "quantity_received"] = df.loc[
        delivered_mask & df["quantity_received"].isna(), "quantity_ordered"
    ]
    df["quantity_received"] = df["quantity_received"].fillna(0).astype(int)

    # 4. Standardize Unit Cost and Recompute Total Spend
    df["unit_cost"] = pd.to_numeric(df["unit_cost"], errors="coerce").fillna(0.0).round(2)
    df["total_spend"] = (df["quantity_ordered"] * df["unit_cost"]).round(2)
    df["fulfilled_spend"] = (df["quantity_received"] * df["unit_cost"]).round(2)

    # 5. Calculate Delivery Delay (Variance in Days)
    # variance = actual_delivery - expected_delivery (0 = on time, <0 = early, >0 = delayed)
    df["delivery_delay_days"] = np.nan
    df.loc[delivered_mask, "delivery_delay_days"] = (
        df.loc[delivered_mask, "actual_delivery"] - df.loc[delivered_mask, "expected_delivery"]
    ).dt.days.astype(int)

    # Order Status Classification
    conditions = [
        df["actual_delivery"].isna() & (pd.Timestamp.now() > df["expected_delivery"]),
        df["actual_delivery"].isna(),
        df["delivery_delay_days"] <= 0,
        df["delivery_delay_days"] > 0,
    ]
    choices = ["Delayed", "In Transit", "On Time", "Delayed"]
    df["order_status"] = np.select(conditions, choices, default="In Transit")

    # 6. Impute Quality Score
    # For delivered items without quality score, impute with category median rating
    category_quality_medians = df.groupby("category")["quality_score"].transform("median")
    df["quality_score"] = pd.to_numeric(df["quality_score"], errors="coerce")
    df.loc[delivered_mask & df["quality_score"].isna(), "quality_score"] = category_quality_medians
    df["quality_score"] = df["quality_score"].round(2)

    # 7. Inventory Stock & Reorder Analysis
    df["stock_on_hand"] = pd.to_numeric(df["stock_on_hand"], errors="coerce").fillna(0).astype(int)
    df["reorder_level"] = pd.to_numeric(df["reorder_level"], errors="coerce").fillna(0).astype(int)
    
    # Calculate stock buffer ratio (stock_on_hand / reorder_level)
    df["stock_reorder_ratio"] = np.where(
        df["reorder_level"] > 0,
        (df["stock_on_hand"] / df["reorder_level"]).round(2),
        np.nan,
    )

    # Stock Health Flag
    stock_conditions = [
        df["stock_on_hand"] < (df["reorder_level"] * 0.5),
        df["stock_on_hand"] <= df["reorder_level"],
        df["stock_reorder_ratio"] > 2.5,
    ]
    stock_choices = ["Critical Shortage", "Reorder Warning", "Slow-Moving"]
    df["inventory_health"] = np.select(stock_conditions, stock_choices, default="Optimal")

    # Format dates back to clean ISO string for standard CSV compatibility
    for col in date_cols:
        df[col] = df[col].dt.strftime("%Y-%m-%d").fillna("")

    # Output directory verification
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"[+] Successfully exported cleaned vendor dataset to: {output_path}")
    print(f"[+] Total spend processed: ${df['total_spend'].sum():,.2f}")
    print(f"[+] Status distribution: {df['order_status'].value_counts().to_dict()}")

    return df


if __name__ == "__main__":
    try:
        clean_vendor_data()
    except Exception as exc:
        print(f"[!] Error during data cleaning: {exc}", file=sys.stderr)
        sys.exit(1)
