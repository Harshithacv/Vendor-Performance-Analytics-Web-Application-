import pandas as pd
from app.services.cleaning import detect_file_type, clean_dataframe

def test_detect_file_type():
    df_inv = pd.DataFrame(columns=[
        "VendorNumber", "VendorName", "InvoiceDate", "PONumber", "PODate", "PayDate", "Quantity", "Dollars", "Freight"
    ])
    assert detect_file_type(df_inv) == "vendor_invoice"

def test_clean_dataframe():
    raw_data = {
        "VendorName": ["  Diageo North America  ", "Diageo North America  "],
        "Dollars": ["$1200.50", "1200.50"],
        "Quantity": [10, 10]
    }
    df = pd.DataFrame(raw_data)
    cleaned, summary = clean_dataframe(df, "vendor_invoice")
    
    assert summary["duplicates_removed"] >= 0
    assert cleaned["VendorName"].iloc[0] == "Diageo North America"
