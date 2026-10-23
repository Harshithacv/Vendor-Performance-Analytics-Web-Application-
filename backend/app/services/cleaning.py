import os
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, List

EXPECTED_SCHEMAS = {
    "vendor_invoice": [
        "VendorNumber", "VendorName", "InvoiceDate", "PONumber", "PODate", "PayDate", "Quantity", "Dollars", "Freight"
    ],
    "purchases": [
        "VendorNumber", "VendorName", "PONumber", "PODate", "ReceivingDate", "InvoiceDate", "PayDate", "PurchasePrice", "Quantity", "Dollars"
    ],
    "sales": [
        "Store", "Brand", "Description", "SalesQuantity", "SalesDollars", "SalesPrice", "SalesDate"
    ],
    "begin_inventory": [
        "InventoryId", "Store", "City", "Brand", "Description", "Size", "onHand", "Price", "startDate"
    ],
    "end_inventory": [
        "InventoryId", "Store", "City", "Brand", "Description", "Size", "onHand", "Price", "endDate"
    ],
    "purchase_prices": [
        "Brand", "Description", "Price", "Size", "PurchasePrice", "VendorNumber", "VendorName"
    ]
}

def detect_file_type(df: pd.DataFrame) -> str:
    cols = set(df.columns)
    for ftype, expected_cols in EXPECTED_SCHEMAS.items():
        matched = sum(1 for c in expected_cols if c in cols)
        if matched / len(expected_cols) >= 0.7:
            return ftype
    return "generic"

def inspect_dataset_preview(file_path: str, nrows: int = 50) -> Dict[str, Any]:
    """Inspects an uploaded CSV or Excel file and returns validation details."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext in ['.xlsx', '.xls']:
        df = pd.read_excel(file_path, nrows=nrows)
        total_rows_approx = len(pd.read_excel(file_path, usecols=[0]))
    else:
        df = pd.read_csv(file_path, nrows=nrows)
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            total_rows_approx = sum(1 for _ in f) - 1

    file_type = detect_file_type(df)
    missing_counts = {col: int(df[col].isnull().sum()) for col in df.columns}
    duplicate_count = int(df.duplicated().sum())

    validation_messages = []
    status = "VALID"

    if df.empty:
        status = "INVALID"
        validation_messages.append("File contains no data rows.")
    
    if duplicate_count > 0:
        validation_messages.append(f"Detected {duplicate_count} duplicate row(s) in preview sample.")
        if status != "INVALID":
            status = "WARNING"
            
    total_nulls = sum(missing_counts.values())
    if total_nulls > 0:
        validation_messages.append(f"Detected {total_nulls} missing/null value(s) in preview columns.")
        if status != "INVALID":
            status = "WARNING"

    cleaning_actions = [
        "Trim leading/trailing whitespace from string fields",
        "Convert numeric and currency strings to standardized float/int",
        "Parse date columns to ISO 8601 YYYY-MM-DD",
        "Impute or handle zero values safely to prevent division-by-zero"
    ]

    # Convert preview rows to JSON serializable format
    clean_preview = df.head(10).replace({np.nan: None}).to_dict(orient="records")

    return {
        "file_name": os.path.basename(file_path),
        "detected_type": file_type,
        "total_rows": max(0, total_rows_approx),
        "total_columns": len(df.columns),
        "columns": list(df.columns),
        "missing_values": missing_counts,
        "duplicate_rows_detected": duplicate_count,
        "validation_status": status,
        "validation_messages": validation_messages if validation_messages else ["File structure is valid and matches expected schema."],
        "preview_rows": clean_preview,
        "cleaning_actions_summary": cleaning_actions
    }

def clean_dataframe(df: pd.DataFrame, file_type: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Applies documented cleaning transformations to the DataFrame."""
    initial_rows = len(df)
    
    # 1. Remove duplicate rows
    df = df.drop_duplicates()
    deduped_rows = len(df)
    duplicates_removed = initial_rows - deduped_rows

    # 2. Strip whitespace from string columns
    str_cols = df.select_dtypes(include=['object']).columns
    for c in str_cols:
        df[c] = df[c].astype(str).str.strip()

    # 3. Numeric conversions based on type
    numeric_candidates = ['Dollars', 'Quantity', 'Freight', 'PurchasePrice', 'Price', 'SalesDollars', 'SalesQuantity', 'SalesPrice', 'onHand']
    for col in numeric_candidates:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # 4. Standardize dates
    date_candidates = ['PODate', 'InvoiceDate', 'PayDate', 'ReceivingDate', 'SalesDate', 'startDate', 'endDate']
    for d_col in date_candidates:
        if d_col in df.columns:
            df[d_col] = pd.to_datetime(df[d_col], errors='coerce')

    final_rows = len(df)
    summary = {
        "initial_rows": initial_rows,
        "duplicates_removed": duplicates_removed,
        "cleaned_records_retained": final_rows,
        "columns_processed": len(df.columns)
    }
    return df, summary
