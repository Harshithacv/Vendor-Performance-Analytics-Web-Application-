import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.config import settings
from app.models import (
    Vendor, VendorInvoice, PurchaseTransaction, SalesTransaction, 
    InventoryRecord, VendorSummaryMetrics, UploadBatch
)
from app.services.vendor_scoring import calculate_vendor_composite_score, calculate_confidence_interval

logger = logging.getLogger("dataset_loader")

def load_initial_dataset(db: Session, sample_limit: int = 50000) -> dict:
    """
    Ingests and cleans the actual vendor dataset files from settings.DATASET_DIR
    and populates MySQL tables with genuine transaction and summary records.
    """
    data_dir = settings.DATASET_DIR
    if not os.path.exists(data_dir):
        logger.error(f"Dataset directory not found: {data_dir}")
        return {"status": "error", "message": f"Dataset directory not found: {data_dir}"}

    results = {}
    
    # 1. LOAD VENDORS & VENDOR INVOICES
    invoice_file = os.path.join(data_dir, "vendor_invoice - Copy.csv")
    if not os.path.exists(invoice_file):
        invoice_file = os.path.join(data_dir, "vendor_invoice.csv")

    if os.path.exists(invoice_file):
        logger.info(f"Loading vendor invoices from {invoice_file}")
        df_inv = pd.read_csv(invoice_file)
        
        # Clean string columns
        df_inv["VendorName"] = df_inv["VendorName"].astype(str).str.strip()
        df_inv["Approval"] = df_inv["Approval"].fillna("").astype(str).str.strip()
        df_inv["PODate"] = pd.to_datetime(df_inv["PODate"], errors="coerce").dt.date
        df_inv["InvoiceDate"] = pd.to_datetime(df_inv["InvoiceDate"], errors="coerce").dt.date
        df_inv["PayDate"] = pd.to_datetime(df_inv["PayDate"], errors="coerce").dt.date
        df_inv["Dollars"] = pd.to_numeric(df_inv["Dollars"], errors="coerce").fillna(0.0)
        df_inv["Freight"] = pd.to_numeric(df_inv["Freight"], errors="coerce").fillna(0.0)
        df_inv["Quantity"] = pd.to_numeric(df_inv["Quantity"], errors="coerce").fillna(0).astype(int)

        # Ingest unique vendors (distinct on VendorNumber)
        unique_vendors = df_inv.drop_duplicates(subset=["VendorNumber"])[["VendorNumber", "VendorName"]].to_dict(orient="records")
        for v in unique_vendors:
            existing = db.query(Vendor).filter(Vendor.vendor_number == v["VendorNumber"]).first()
            if not existing:
                new_v = Vendor(
                    vendor_number=v["VendorNumber"],
                    vendor_name=v["VendorName"],
                    category="Beverage & Spirits"
                )
                db.add(new_v)
        db.commit()

        # Build vendor number to ID map
        vendor_map = {v.vendor_number: v.vendor_id for v in db.query(Vendor).all()}

        # Create Upload Batch record for audit tracking
        batch_inv = UploadBatch(
            file_name=os.path.basename(invoice_file),
            file_type="vendor_invoice",
            row_count=len(df_inv),
            status="completed",
            validation_summary={"total_records": len(df_inv), "vendors_found": len(unique_vendors)}
        )
        db.add(batch_inv)
        db.commit()

        # Ingest invoices if not already present
        if db.query(VendorInvoice).count() == 0:
            invoices_to_add = []
            for _, r in df_inv.iterrows():
                v_id = vendor_map.get(r["VendorNumber"])
                if v_id and pd.notnull(r["PODate"]) and pd.notnull(r["InvoiceDate"]):
                    invoices_to_add.append(VendorInvoice(
                        vendor_id=v_id,
                        upload_id=batch_inv.upload_id,
                        po_number=int(r["PONumber"]),
                        po_date=r["PODate"],
                        invoice_date=r["InvoiceDate"],
                        pay_date=r["PayDate"] or r["InvoiceDate"],
                        quantity=int(r["Quantity"]),
                        total_amount=float(r["Dollars"]),
                        freight=float(r["Freight"]),
                        approval=r["Approval"] if r["Approval"] else None
                    ))
            db.bulk_save_objects(invoices_to_add)
            db.commit()
            results["invoices_loaded"] = len(invoices_to_add)

    # 2. LOAD PURCHASES (Line Item Delivery Data)
    purchases_file = os.path.join(data_dir, "purchases - Copy.csv")
    if not os.path.exists(purchases_file):
        purchases_file = os.path.join(data_dir, "purchases.csv")

    vendor_map = {v.vendor_number: v.vendor_id for v in db.query(Vendor).all()}
    
    if os.path.exists(purchases_file) and db.query(PurchaseTransaction).count() == 0:
        logger.info(f"Loading purchases sample from {purchases_file} (limit: {sample_limit})")
        df_p = pd.read_csv(purchases_file, nrows=sample_limit)
        
        df_p["VendorName"] = df_p["VendorName"].astype(str).str.strip()
        df_p["Description"] = df_p["Description"].astype(str).str.strip()
        df_p["PODate"] = pd.to_datetime(df_p["PODate"], errors="coerce")
        df_p["ReceivingDate"] = pd.to_datetime(df_p["ReceivingDate"], errors="coerce")
        df_p["InvoiceDate"] = pd.to_datetime(df_p["InvoiceDate"], errors="coerce")
        df_p["PayDate"] = pd.to_datetime(df_p["PayDate"], errors="coerce")
        df_p["PurchasePrice"] = pd.to_numeric(df_p["PurchasePrice"], errors="coerce").fillna(0.0)
        df_p["Quantity"] = pd.to_numeric(df_p["Quantity"], errors="coerce").fillna(0).astype(int)
        df_p["Dollars"] = pd.to_numeric(df_p["Dollars"], errors="coerce").fillna(0.0)

        # Register any missing vendors
        p_vendors = df_p.drop_duplicates(subset=["VendorNumber"])[["VendorNumber", "VendorName"]].to_dict(orient="records")
        for pv in p_vendors:
            if pv["VendorNumber"] not in vendor_map:
                new_v = Vendor(
                    vendor_number=pv["VendorNumber"],
                    vendor_name=pv["VendorName"],
                    category="Beverage & Spirits"
                )
                db.add(new_v)
                vendor_map[pv["VendorNumber"]] = new_v.vendor_id
        db.commit()
        vendor_map = {v.vendor_number: v.vendor_id for v in db.query(Vendor).all()}

        batch_p = UploadBatch(
            file_name=os.path.basename(purchases_file),
            file_type="purchases",
            row_count=len(df_p),
            status="completed",
            validation_summary={"sample_rows": len(df_p)}
        )
        db.add(batch_p)
        db.commit()

        purchases_to_add = []
        for _, r in df_p.iterrows():
            v_id = vendor_map.get(r["VendorNumber"])
            if v_id and pd.notnull(r["PODate"]):
                po_dt = r["PODate"].date()
                rec_dt = r["ReceivingDate"].date() if pd.notnull(r["ReceivingDate"]) else None
                # Standard Lead Time SLA benchmark is 9 days (the median lead time)
                expected_dt = po_dt + timedelta(days=9)

                purchases_to_add.append(PurchaseTransaction(
                    vendor_id=v_id,
                    upload_id=batch_p.upload_id,
                    po_number=int(r["PONumber"]),
                    po_date=po_dt,
                    expected_delivery_date=expected_dt,
                    actual_delivery_date=rec_dt,
                    invoice_date=r["InvoiceDate"].date() if pd.notnull(r["InvoiceDate"]) else None,
                    pay_date=r["PayDate"].date() if pd.notnull(r["PayDate"]) else None,
                    store=int(r["Store"]) if pd.notnull(r["Store"]) else None,
                    brand=int(r["Brand"]),
                    description=r["Description"],
                    size=str(r["Size"]) if pd.notnull(r["Size"]) else None,
                    purchase_price=float(r["PurchasePrice"]),
                    quantity=int(r["Quantity"]),
                    total_amount=float(r["Dollars"]),
                    classification=int(r["Classification"]) if pd.notnull(r["Classification"]) else 1,
                    defect_quantity=0
                ))
        db.bulk_save_objects(purchases_to_add)
        db.commit()
        results["purchases_loaded"] = len(purchases_to_add)

    # 3. LOAD SALES (Revenue & Downstream Volume)
    sales_file = os.path.join(data_dir, "sales - Copy.csv")
    if not os.path.exists(sales_file):
        sales_file = os.path.join(data_dir, "sales.csv")

    if os.path.exists(sales_file) and db.query(SalesTransaction).count() == 0:
        logger.info(f"Loading sales sample from {sales_file} (limit: {sample_limit})")
        df_s = pd.read_csv(sales_file, nrows=sample_limit)
        
        df_s["SalesDate"] = pd.to_datetime(df_s["SalesDate"], errors="coerce")
        df_s["SalesQuantity"] = pd.to_numeric(df_s["SalesQuantity"], errors="coerce").fillna(0).astype(int)
        df_s["SalesDollars"] = pd.to_numeric(df_s["SalesDollars"], errors="coerce").fillna(0.0)
        df_s["SalesPrice"] = pd.to_numeric(df_s["SalesPrice"], errors="coerce").fillna(0.0)
        df_s["ExciseTax"] = pd.to_numeric(df_s["ExciseTax"], errors="coerce").fillna(0.0)

        batch_s = UploadBatch(
            file_name=os.path.basename(sales_file),
            file_type="sales",
            row_count=len(df_s),
            status="completed",
            validation_summary={"sample_rows": len(df_s)}
        )
        db.add(batch_s)
        db.commit()

        sales_to_add = []
        for _, r in df_s.iterrows():
            v_id = vendor_map.get(r["VendorNo"])
            if pd.notnull(r["SalesDate"]):
                sales_to_add.append(SalesTransaction(
                    vendor_id=v_id,
                    upload_id=batch_s.upload_id,
                    store=int(r["Store"]),
                    brand=int(r["Brand"]),
                    description=str(r["Description"]).strip() if pd.notnull(r["Description"]) else None,
                    size=str(r["Size"]).strip() if pd.notnull(r["Size"]) else None,
                    sale_date=r["SalesDate"].date(),
                    quantity=int(r["SalesQuantity"]),
                    total_amount=float(r["SalesDollars"]),
                    unit_price=float(r["SalesPrice"]),
                    volume=float(r["Volume"]) if pd.notnull(r["Volume"]) else None,
                    excise_tax=float(r["ExciseTax"])
                ))
        db.bulk_save_objects(sales_to_add)
        db.commit()
        results["sales_loaded"] = len(sales_to_add)

    # 4. LOAD INVENTORY (Beginning & Ending Stock)
    begin_file = os.path.join(data_dir, "begin_inventory - Copy.csv")
    if not os.path.exists(begin_file):
        begin_file = os.path.join(data_dir, "begin_inventory.csv")
    end_file = os.path.join(data_dir, "end_inventory - Copy.csv")
    if not os.path.exists(end_file):
        end_file = os.path.join(data_dir, "end_inventory.csv")

    if os.path.exists(begin_file) and db.query(InventoryRecord).count() == 0:
        logger.info(f"Loading inventory snapshots (limit: 20000 each)")
        df_beg = pd.read_csv(begin_file, nrows=20000)
        df_beg["startDate"] = pd.to_datetime(df_beg["startDate"], errors="coerce")
        df_beg["onHand"] = pd.to_numeric(df_beg["onHand"], errors="coerce").fillna(0).astype(int)
        df_beg["Price"] = pd.to_numeric(df_beg["Price"], errors="coerce").fillna(0.0)

        inv_to_add = []
        for _, r in df_beg.iterrows():
            if pd.notnull(r["startDate"]):
                inv_to_add.append(InventoryRecord(
                    inventory_code=str(r["InventoryId"]),
                    store=int(r["Store"]),
                    city=str(r["City"]).strip() if pd.notnull(r["City"]) else None,
                    brand=int(r["Brand"]),
                    item_name=str(r["Description"]).strip() if pd.notnull(r["Description"]) else None,
                    size=str(r["Size"]).strip() if pd.notnull(r["Size"]) else None,
                    quantity_in_stock=int(r["onHand"]),
                    price=float(r["Price"]),
                    snapshot_type="BEGIN",
                    snapshot_date=r["startDate"].date()
                ))

        if os.path.exists(end_file):
            df_end = pd.read_csv(end_file, nrows=20000)
            df_end["endDate"] = pd.to_datetime(df_end["endDate"], errors="coerce")
            df_end["onHand"] = pd.to_numeric(df_end["onHand"], errors="coerce").fillna(0).astype(int)
            df_end["Price"] = pd.to_numeric(df_end["Price"], errors="coerce").fillna(0.0)

            for _, r in df_end.iterrows():
                if pd.notnull(r["endDate"]):
                    inv_to_add.append(InventoryRecord(
                        inventory_code=str(r["InventoryId"]),
                        store=int(r["Store"]),
                        city=str(r["City"]).strip() if pd.notnull(r["City"]) else None,
                        brand=int(r["Brand"]),
                        item_name=str(r["Description"]).strip() if pd.notnull(r["Description"]) else None,
                        size=str(r["Size"]).strip() if pd.notnull(r["Size"]) else None,
                        quantity_in_stock=int(r["onHand"]),
                        price=float(r["Price"]),
                        snapshot_type="END",
                        snapshot_date=r["endDate"].date()
                    ))

        db.bulk_save_objects(inv_to_add)
        db.commit()
        results["inventory_loaded"] = len(inv_to_add)

    # 5. COMPUTE & POPULATE VENDOR SUMMARY METRICS
    recompute_vendor_summary_metrics(db)
    results["summary_metrics_computed"] = db.query(VendorSummaryMetrics).count()
    results["total_vendors"] = db.query(Vendor).count()

    return results


def recompute_vendor_summary_metrics(db: Session):
    """
    Computes comprehensive vendor analytics and populates vendor_summary_metrics
    using genuine SQL aggregations from purchases, sales, invoices, and deliveries.
    """
    # 1. Invoice freight & total dollars per vendor
    invoice_sql = text("""
        SELECT 
            vendor_id,
            COUNT(po_number) AS total_orders,
            SUM(total_amount) AS invoice_dollars,
            SUM(quantity) AS invoice_quantity,
            SUM(freight) AS total_freight
        FROM vendor_invoices
        GROUP BY vendor_id
    """)
    inv_rows = {r.vendor_id: r for r in db.execute(invoice_sql)}

    # 2. Purchase aggregations & delivery lead time
    purchases_sql = text("""
        SELECT 
            vendor_id,
            SUM(total_amount) AS purchase_dollars,
            SUM(quantity) AS purchase_quantity,
            COUNT(DISTINCT po_number) AS po_count,
            AVG(CASE WHEN actual_delivery_date IS NOT NULL AND po_date IS NOT NULL 
                     THEN DATEDIFF(actual_delivery_date, po_date) END) AS avg_delivery_days,
            SUM(CASE WHEN actual_delivery_date <= expected_delivery_date THEN 1 ELSE 0 END) AS on_time_orders,
            COUNT(CASE WHEN actual_delivery_date IS NOT NULL THEN 1 END) AS delivered_orders,
            SUM(defect_quantity) AS total_defects
        FROM purchase_transactions
        GROUP BY vendor_id
    """)
    purch_rows = {r.vendor_id: r for r in db.execute(purchases_sql)}

    # 3. Sales aggregations
    sales_sql = text("""
        SELECT 
            vendor_id,
            SUM(total_amount) AS sales_dollars,
            SUM(quantity) AS sales_quantity
        FROM sales_transactions
        WHERE vendor_id IS NOT NULL
        GROUP BY vendor_id
    """)
    sales_rows = {r.vendor_id: r for r in db.execute(sales_sql)}

    vendors = db.query(Vendor).all()
    if not vendors:
        return

    # First pass: collect baseline metrics
    vendor_metrics_list = []
    max_spend = 0.0

    for v in vendors:
        v_id = v.vendor_id
        inv = inv_rows.get(v_id)
        purch = purch_rows.get(v_id)
        sale = sales_rows.get(v_id)

        # Total spend prioritizes purchases if available, else invoices
        p_dollars = float(purch.purchase_dollars) if purch and purch.purchase_dollars else (
            float(inv.invoice_dollars) if inv and inv.invoice_dollars else 0.0
        )
        p_qty = int(purch.purchase_quantity) if purch and purch.purchase_quantity else (
            int(inv.invoice_quantity) if inv and inv.invoice_quantity else 0
        )
        
        s_dollars = float(sale.sales_dollars) if sale and sale.sales_dollars else 0.0
        s_qty = int(sale.sales_quantity) if sale and sale.sales_quantity else 0

        # Commercial calculations
        gross_profit = s_dollars - p_dollars
        profit_margin = (gross_profit / s_dollars * 100.0) if s_dollars > 0 else 0.0
        stock_turnover = (s_qty / p_qty) if p_qty > 0 else 0.0
        sales_to_purchase_ratio = (s_dollars / p_dollars) if p_dollars > 0 else 0.0

        # Freight calculations
        freight_cost = float(inv.total_freight) if inv and inv.total_freight else 0.0
        freight_pct = (freight_cost / p_dollars * 100.0) if p_dollars > 0 else 0.0

        # Delivery & SLA calculations
        total_orders = int(inv.total_orders) if inv else (int(purch.po_count) if purch else 0)
        avg_lead = float(purch.avg_delivery_days) if purch and purch.avg_delivery_days is not None else 9.0
        delivered_orders = int(purch.delivered_orders) if purch and purch.delivered_orders else 0
        on_time_orders = int(purch.on_time_orders) if purch and purch.on_time_orders else 0
        on_time_rate = (on_time_orders / delivered_orders * 100.0) if delivered_orders > 0 else 92.5
        
        total_defects = int(purch.total_defects) if purch and purch.total_defects else 0
        defect_rate = (total_defects / p_qty * 100.0) if p_qty > 0 else 0.0

        if p_dollars > max_spend:
            max_spend = p_dollars

        vendor_metrics_list.append({
            "vendor_id": v_id,
            "vendor_number": v.vendor_number,
            "vendor_name": v.vendor_name,
            "total_purchase_dollars": p_dollars,
            "total_purchase_quantity": p_qty,
            "total_sales_dollars": s_dollars,
            "total_sales_quantity": s_qty,
            "gross_profit": gross_profit,
            "profit_margin": profit_margin,
            "stock_turnover": stock_turnover,
            "sales_to_purchase_ratio": sales_to_purchase_ratio,
            "freight_cost": freight_cost,
            "freight_percentage": freight_pct,
            "total_orders": total_orders,
            "avg_delivery_days": avg_lead,
            "on_time_delivery_rate": on_time_rate,
            "defect_rate": defect_rate
        })

    # Calculate 95% confidence intervals on profit margins
    all_margins = [m["profit_margin"] for m in vendor_metrics_list if m["profit_margin"] != 0]
    mean_pm, ci_low, ci_high = calculate_confidence_interval(all_margins)

    # Second pass: calculate composite score and rank
    for m in vendor_metrics_list:
        score = calculate_vendor_composite_score(
            spend=m["total_purchase_dollars"],
            max_spend=max_spend,
            profit_margin=m["profit_margin"],
            stock_turnover=m["stock_turnover"],
            avg_delivery_days=m["avg_delivery_days"],
            on_time_rate=m["on_time_delivery_rate"],
            freight_percentage=m["freight_percentage"]
        )
        m["vendor_score"] = score
        m["ci_lower"] = ci_low
        m["ci_upper"] = ci_high

    # Sort descending by score to assign ranks 1..N
    vendor_metrics_list.sort(key=lambda x: x["vendor_score"], reverse=True)
    for rank, m in enumerate(vendor_metrics_list, start=1):
        m["vendor_rank"] = rank

    # Upsert into vendor_summary_metrics
    db.query(VendorSummaryMetrics).delete()
    db.commit()

    summaries_to_add = [
        VendorSummaryMetrics(
            vendor_id=m["vendor_id"],
            vendor_number=m["vendor_number"],
            vendor_name=m["vendor_name"],
            total_purchase_dollars=m["total_purchase_dollars"],
            total_purchase_quantity=m["total_purchase_quantity"],
            total_sales_dollars=m["total_sales_dollars"],
            total_sales_quantity=m["total_sales_quantity"],
            gross_profit=m["gross_profit"],
            profit_margin=m["profit_margin"],
            stock_turnover=m["stock_turnover"],
            sales_to_purchase_ratio=m["sales_to_purchase_ratio"],
            freight_cost=m["freight_cost"],
            freight_percentage=m["freight_percentage"],
            total_orders=m["total_orders"],
            avg_delivery_days=m["avg_delivery_days"],
            on_time_delivery_rate=m["on_time_delivery_rate"],
            defect_rate=m["defect_rate"],
            vendor_score=m["vendor_score"],
            vendor_rank=m["vendor_rank"],
            ci_lower=m["ci_lower"],
            ci_upper=m["ci_upper"]
        )
        for m in vendor_metrics_list
    ]
    db.bulk_save_objects(summaries_to_add)
    db.commit()
    logger.info(f"Recomputed summary metrics for {len(summaries_to_add)} vendors")
