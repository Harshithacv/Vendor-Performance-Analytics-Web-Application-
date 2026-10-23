import io
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models import VendorSummaryMetrics, VendorInvoice, PurchaseTransaction, SalesTransaction, InventoryRecord

def export_data_to_csv(db: Session, report_type: str, vendor_id: int = None) -> io.StringIO:
    """Generates an in-memory CSV stream based on report type and filters."""
    output = io.StringIO()
    
    if report_type == "vendors":
        query = db.query(VendorSummaryMetrics)
        if vendor_id:
            query = query.filter(VendorSummaryMetrics.vendor_id == vendor_id)
        rows = query.order_by(VendorSummaryMetrics.vendor_rank).all()
        data = [
            {
                "Rank": r.vendor_rank,
                "Vendor Number": r.vendor_number,
                "Vendor Name": r.vendor_name,
                "Score": float(r.vendor_score),
                "Procurement Spend ($)": float(r.total_purchase_dollars),
                "Sales Revenue ($)": float(r.total_sales_dollars),
                "Gross Profit ($)": float(r.gross_profit),
                "Profit Margin (%)": float(r.profit_margin),
                "Stock Turnover": float(r.stock_turnover),
                "Avg Delivery Days": float(r.avg_delivery_days),
                "On-Time Rate (%)": float(r.on_time_delivery_rate),
                "Freight Cost ($)": float(r.freight_cost),
                "Total POs": r.total_orders
            }
            for r in rows
        ]
        df = pd.DataFrame(data)
    elif report_type == "purchases":
        sql = text("""
            SELECT 
                v.vendor_name,
                pt.po_number,
                pt.po_date,
                pt.actual_delivery_date,
                pt.brand,
                pt.description,
                pt.quantity,
                pt.purchase_price,
                pt.total_amount
            FROM purchase_transactions pt
            JOIN vendors v ON pt.vendor_id = v.vendor_id
            """ + ("WHERE pt.vendor_id = :v_id" if vendor_id else "") + """
            ORDER BY pt.po_date DESC
            LIMIT 5000
        """)
        params = {"v_id": vendor_id} if vendor_id else {}
        records = db.execute(sql, params).fetchall()
        df = pd.DataFrame(records, columns=[
            "Vendor", "PO Number", "Order Date", "Delivery Date", "Brand", 
            "Description", "Quantity", "Unit Price", "Total Amount"
        ])
    elif report_type == "inventory":
        records = db.query(InventoryRecord).order_by(InventoryRecord.store, InventoryRecord.brand).limit(5000).all()
        data = [
            {
                "Inventory Code": r.inventory_code,
                "Store": r.store,
                "City": r.city,
                "Brand": r.brand,
                "Item Name": r.item_name,
                "Size": r.size,
                "Quantity on Hand": r.quantity_in_stock,
                "Unit Price": float(r.price),
                "Inventory Value": float(r.quantity_in_stock * r.price),
                "Snapshot Type": r.snapshot_type,
                "Snapshot Date": str(r.snapshot_date)
            }
            for r in records
        ]
        df = pd.DataFrame(data)
    else:
        # Default invoices
        query = db.query(VendorInvoice)
        if vendor_id:
            query = query.filter(VendorInvoice.vendor_id == vendor_id)
        records = query.order_by(VendorInvoice.po_date.desc()).limit(5000).all()
        data = [
            {
                "PO Number": r.po_number,
                "Order Date": str(r.po_date),
                "Invoice Date": str(r.invoice_date),
                "Quantity": r.quantity,
                "Total Amount ($)": float(r.total_amount),
                "Freight ($)": float(r.freight),
                "Approval": r.approval
            }
            for r in records
        ]
        df = pd.DataFrame(data)

    df.to_csv(output, index=False)
    output.seek(0)
    return output
