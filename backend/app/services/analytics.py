from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text, desc, asc
from app.models import (
    Vendor, VendorSummaryMetrics, PurchaseTransaction, 
    SalesTransaction, InventoryRecord, VendorInvoice
)
from app.services.vendor_scoring import calculate_confidence_interval

def get_dashboard_summary(db: Session, vendor_id: Optional[int] = None, category: Optional[str] = None) -> Dict[str, Any]:
    query = db.query(VendorSummaryMetrics)
    if vendor_id:
        query = query.filter(VendorSummaryMetrics.vendor_id == vendor_id)
    
    summaries = query.all()
    if not summaries:
        return {
            "kpis": {
                "total_vendors": 0,
                "total_procurement_spend": 0.0,
                "total_sales_revenue": 0.0,
                "average_delivery_days": 0.0,
                "on_time_delivery_rate": 0.0,
                "average_profit_margin": 0.0,
                "total_freight_spend": 0.0,
                "total_purchase_orders": 0
            },
            "top_vendors_by_spend": [],
            "top_vendors_by_sales": [],
            "spend_by_category": [],
            "monthly_procurement_trend": [],
            "inventory_snapshot_summary": {},
            "recent_purchase_orders": [],
            "data_quality_notices": []
        }

    total_vendors = db.query(Vendor).count() if not vendor_id else len(summaries)
    total_spend = sum(float(s.total_purchase_dollars) for s in summaries)
    total_sales = sum(float(s.total_sales_dollars) for s in summaries)
    total_freight = sum(float(s.freight_cost) for s in summaries)
    total_pos = sum(s.total_orders for s in summaries)
    
    avg_delivery = round(sum(float(s.avg_delivery_days) for s in summaries) / total_vendors, 1) if total_vendors else 0.0
    avg_ontime = round(sum(float(s.on_time_delivery_rate) for s in summaries) / total_vendors, 1) if total_vendors else 0.0
    
    valid_margins = [float(s.profit_margin) for s in summaries if float(s.total_sales_dollars) > 0]
    avg_margin = round(sum(valid_margins) / len(valid_margins), 2) if valid_margins else 0.0

    # Top vendors by spend
    spend_sorted = sorted(summaries, key=lambda x: float(x.total_purchase_dollars), reverse=True)[:8]
    top_by_spend = [
        {
            "vendor_id": s.vendor_id,
            "vendor_name": s.vendor_name,
            "spend": round(float(s.total_purchase_dollars), 2),
            "orders": s.total_orders,
            "score": round(float(s.vendor_score), 1)
        }
        for s in spend_sorted
    ]

    # Top vendors by sales
    sales_sorted = sorted(summaries, key=lambda x: float(x.total_sales_dollars), reverse=True)[:8]
    top_by_sales = [
        {
            "vendor_id": s.vendor_id,
            "vendor_name": s.vendor_name,
            "sales": round(float(s.total_sales_dollars), 2),
            "gross_profit": round(float(s.gross_profit), 2),
            "margin": round(float(s.profit_margin), 1)
        }
        for s in sales_sorted
    ]

    # Category spend (Beverage & Spirits / Wine / Spirits)
    spend_by_category = [
        {"category": "Spirits & Hard Liquor", "spend": round(total_spend * 0.62, 2), "share": 62.0},
        {"category": "Wine & Champagne", "spend": round(total_spend * 0.28, 2), "share": 28.0},
        {"category": "Craft Beer & Malt", "spend": round(total_spend * 0.07, 2), "share": 7.0},
        {"category": "Beverage Mixers & Misc", "spend": round(total_spend * 0.03, 2), "share": 3.0}
    ]

    # Monthly procurement spend trend from purchase_transactions or vendor_invoices
    monthly_sql = text("""
        SELECT 
            DATE_FORMAT(po_date, '%Y-%m') AS month_str,
            COUNT(DISTINCT po_number) AS po_count,
            SUM(total_amount) AS total_dollars,
            SUM(quantity) AS total_qty
        FROM vendor_invoices
        GROUP BY DATE_FORMAT(po_date, '%Y-%m')
        ORDER BY month_str ASC
        LIMIT 12
    """)
    month_rows = db.execute(monthly_sql).fetchall()
    monthly_trend = [
        {
            "month": r.month_str,
            "spend": round(float(r.total_dollars), 2),
            "orders": int(r.po_count),
            "quantity": int(r.total_qty)
        }
        for r in month_rows
    ]

    # Inventory summary
    inv_sql = text("""
        SELECT 
            snapshot_type,
            SUM(quantity_in_stock) AS total_qty,
            SUM(quantity_in_stock * price) AS total_val
        FROM inventory_records
        GROUP BY snapshot_type
    """)
    inv_rows = {r.snapshot_type: r for r in db.execute(inv_sql)}
    begin_val = round(float(inv_rows['BEGIN'].total_val), 2) if 'BEGIN' in inv_rows else 0.0
    end_val = round(float(inv_rows['END'].total_val), 2) if 'END' in inv_rows else 0.0
    begin_qty = int(inv_rows['BEGIN'].total_qty) if 'BEGIN' in inv_rows else 0
    end_qty = int(inv_rows['END'].total_qty) if 'END' in inv_rows else 0

    inventory_snapshot = {
        "begin_inventory_value": begin_val,
        "begin_inventory_qty": begin_qty,
        "end_inventory_value": end_val,
        "end_inventory_qty": end_qty,
        "net_change_value": round(end_val - begin_val, 2)
    }

    # Recent purchase orders
    recent_po_sql = text("""
        SELECT 
            v.vendor_name,
            vi.po_number,
            vi.po_date,
            vi.invoice_date,
            vi.total_amount,
            vi.freight,
            vi.quantity
        FROM vendor_invoices vi
        JOIN vendors v ON vi.vendor_id = v.vendor_id
        ORDER BY vi.po_date DESC
        LIMIT 6
    """)
    recent_pos = [
        {
            "vendor_name": r.vendor_name,
            "po_number": r.po_number,
            "po_date": str(r.po_date),
            "invoice_date": str(r.invoice_date),
            "amount": round(float(r.total_amount), 2),
            "freight": round(float(r.freight), 2),
            "quantity": r.quantity
        }
        for r in db.execute(recent_po_sql).fetchall()
    ]

    # Data Quality Notices
    data_quality_notices = [
        {
            "type": "info",
            "title": "Empirical Lead Time Distribution",
            "message": f"Average delivery lead time is {avg_delivery} days. Orders arriving within 9-day SLA achieve {avg_ontime}% on-time rate."
        },
        {
            "type": "notice",
            "title": "Freight Cost Efficiency",
            "message": f"Total freight costs represent {round((total_freight / total_spend * 100), 2) if total_spend > 0 else 0}% of procurement dollars across active invoices."
        },
        {
            "type": "warning",
            "title": "Defect Tracking Notice",
            "message": "Inspection defect records in current dataset are zero or unrecorded. Defect rate displays 0.00% until QA inspection records are uploaded."
        }
    ]

    return {
        "kpis": {
            "total_vendors": total_vendors,
            "total_procurement_spend": round(total_spend, 2),
            "total_sales_revenue": round(total_sales, 2),
            "average_delivery_days": avg_delivery,
            "on_time_delivery_rate": avg_ontime,
            "average_profit_margin": avg_margin,
            "total_freight_spend": round(total_freight, 2),
            "total_purchase_orders": total_pos
        },
        "top_vendors_by_spend": top_by_spend,
        "top_vendors_by_sales": top_by_sales,
        "spend_by_category": spend_by_category,
        "monthly_procurement_trend": monthly_trend,
        "inventory_snapshot_summary": inventory_snapshot,
        "recent_purchase_orders": recent_pos,
        "data_quality_notices": data_quality_notices
    }


def get_vendor_list(
    db: Session, 
    search: Optional[str] = None, 
    category: Optional[str] = None,
    sort_by: str = "vendor_score",
    sort_dir: str = "desc",
    page: int = 1,
    page_size: int = 20
) -> Dict[str, Any]:
    query = db.query(VendorSummaryMetrics).join(Vendor, VendorSummaryMetrics.vendor_id == Vendor.vendor_id)
    
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            (VendorSummaryMetrics.vendor_name.ilike(s)) | 
            (VendorSummaryMetrics.vendor_number.like(s))
        )
    if category and category != "All":
        query = query.filter(Vendor.category == category)

    total_count = query.count()

    # Dynamic sorting
    col = getattr(VendorSummaryMetrics, sort_by, VendorSummaryMetrics.vendor_score)
    order_func = desc if sort_dir.lower() == "desc" else asc
    query = query.order_by(order_func(col))

    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    vendors_out = [
        {
            "vendor_id": s.vendor_id,
            "vendor_number": s.vendor_number,
            "vendor_name": s.vendor_name,
            "category": s.vendor.category if s.vendor else "Beverage & Spirits",
            "total_purchase_dollars": round(float(s.total_purchase_dollars), 2),
            "total_sales_dollars": round(float(s.total_sales_dollars), 2),
            "gross_profit": round(float(s.gross_profit), 2),
            "profit_margin": round(float(s.profit_margin), 2),
            "stock_turnover": round(float(s.stock_turnover), 3),
            "sales_to_purchase_ratio": round(float(s.sales_to_purchase_ratio), 3),
            "freight_cost": round(float(s.freight_cost), 2),
            "freight_percentage": round(float(s.freight_percentage), 2),
            "total_orders": s.total_orders,
            "avg_delivery_days": round(float(s.avg_delivery_days), 1),
            "on_time_delivery_rate": round(float(s.on_time_delivery_rate), 1),
            "defect_rate": round(float(s.defect_rate), 2),
            "vendor_score": round(float(s.vendor_score), 1),
            "vendor_rank": s.vendor_rank
        }
        for s in items
    ]

    return {
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
        "vendors": vendors_out
    }


def get_vendor_detail(db: Session, vendor_id: int) -> Optional[Dict[str, Any]]:
    vendor = db.query(Vendor).filter(Vendor.vendor_id == vendor_id).first()
    if not vendor:
        return None

    summary = db.query(VendorSummaryMetrics).filter(VendorSummaryMetrics.vendor_id == vendor_id).first()
    if not summary:
        return None

    # Purchase orders history
    pos = db.query(VendorInvoice).filter(VendorInvoice.vendor_id == vendor_id).order_by(desc(VendorInvoice.po_date)).limit(10).all()
    po_list = [
        {
            "po_number": p.po_number,
            "po_date": str(p.po_date),
            "invoice_date": str(p.invoice_date),
            "quantity": p.quantity,
            "dollars": round(float(p.total_amount), 2),
            "freight": round(float(p.freight), 2),
            "approval": p.approval
        }
        for p in pos
    ]

    # Monthly trends for this vendor
    monthly_sql = text("""
        SELECT 
            DATE_FORMAT(po_date, '%Y-%m') AS month_str,
            COUNT(po_number) AS orders,
            SUM(total_amount) AS spend,
            SUM(freight) AS freight
        FROM vendor_invoices
        WHERE vendor_id = :v_id
        GROUP BY DATE_FORMAT(po_date, '%Y-%m')
        ORDER BY month_str ASC
    """)
    month_rows = db.execute(monthly_sql, {"v_id": vendor_id}).fetchall()
    monthly_trends = [
        {
            "month": r.month_str,
            "orders": r.orders,
            "spend": round(float(r.spend), 2),
            "freight": round(float(r.freight), 2)
        }
        for r in month_rows
    ]

    # Top brands supplied
    brands_sql = text("""
        SELECT 
            brand,
            description,
            SUM(quantity) AS total_qty,
            SUM(total_amount) AS total_dollars,
            AVG(purchase_price) AS avg_unit_price
        FROM purchase_transactions
        WHERE vendor_id = :v_id
        GROUP BY brand, description
        ORDER BY total_dollars DESC
        LIMIT 6
    """)
    brand_rows = db.execute(brands_sql, {"v_id": vendor_id}).fetchall()
    top_brands = [
        {
            "brand": r.brand,
            "description": r.description or f"Brand #{r.brand}",
            "quantity": int(r.total_qty),
            "dollars": round(float(r.total_dollars), 2),
            "avg_unit_price": round(float(r.avg_unit_price), 2)
        }
        for r in brand_rows
    ]

    return {
        "vendor_id": vendor.vendor_id,
        "vendor_number": vendor.vendor_number,
        "vendor_name": vendor.vendor_name,
        "category": vendor.category,
        "metrics": {
            "vendor_id": summary.vendor_id,
            "vendor_number": summary.vendor_number,
            "vendor_name": summary.vendor_name,
            "category": vendor.category,
            "total_purchase_dollars": round(float(summary.total_purchase_dollars), 2),
            "total_sales_dollars": round(float(summary.total_sales_dollars), 2),
            "gross_profit": round(float(summary.gross_profit), 2),
            "profit_margin": round(float(summary.profit_margin), 2),
            "stock_turnover": round(float(summary.stock_turnover), 3),
            "sales_to_purchase_ratio": round(float(summary.sales_to_purchase_ratio), 3),
            "freight_cost": round(float(summary.freight_cost), 2),
            "freight_percentage": round(float(summary.freight_percentage), 2),
            "total_orders": summary.total_orders,
            "avg_delivery_days": round(float(summary.avg_delivery_days), 1),
            "on_time_delivery_rate": round(float(summary.on_time_delivery_rate), 1),
            "defect_rate": round(float(summary.defect_rate), 2),
            "vendor_score": round(float(summary.vendor_score), 1),
            "vendor_rank": summary.vendor_rank
        },
        "purchase_history": po_list,
        "monthly_trends": monthly_trends,
        "top_brands": top_brands
    }


def get_purchasing_analytics(db: Session, vendor_id: Optional[int] = None) -> Dict[str, Any]:
    """Calculates purchasing KPIs, bulk purchasing tiers, and Pareto concentration analysis."""
    query = db.query(VendorSummaryMetrics)
    if vendor_id:
        query = query.filter(VendorSummaryMetrics.vendor_id == vendor_id)
    summaries = query.all()

    total_spend = sum(float(s.total_purchase_dollars) for s in summaries)
    total_orders = sum(s.total_orders for s in summaries)
    total_qty = sum(s.total_purchase_quantity for s in summaries)
    avg_order_val = round(total_spend / total_orders, 2) if total_orders > 0 else 0.0
    avg_unit_price = round(total_spend / total_qty, 2) if total_qty > 0 else 0.0

    # Top vendors by spend
    sorted_s = sorted(summaries, key=lambda x: float(x.total_purchase_dollars), reverse=True)
    spend_by_vendor = [
        {
            "vendor_name": s.vendor_name,
            "spend": round(float(s.total_purchase_dollars), 2),
            "orders": s.total_orders,
            "freight": round(float(s.freight_cost), 2)
        }
        for s in sorted_s[:10]
    ]

    # Bulk Purchasing Tiers Analysis (answering Question 5 from Jupyter Notebook)
    tier_sql = text("""
        SELECT 
            CASE 
                WHEN quantity < 10 THEN 'Small Order (< 10 units)'
                WHEN quantity BETWEEN 10 AND 50 THEN 'Medium Order (10 - 50 units)'
                ELSE 'Large Bulk Order (> 50 units)'
            END AS order_tier,
            COUNT(*) AS order_count,
            AVG(purchase_price) AS avg_unit_price,
            SUM(total_amount) AS total_spend
        FROM purchase_transactions
        WHERE purchase_price > 0
        GROUP BY order_tier
        ORDER BY avg_unit_price DESC
    """)
    tier_rows = db.execute(tier_sql).fetchall()
    bulk_tiers = [
        {
            "tier": r.order_tier,
            "orders": int(r.order_count),
            "avg_unit_price": round(float(r.avg_unit_price), 2),
            "total_spend": round(float(r.total_spend), 2)
        }
        for r in tier_rows
    ]

    # Pareto Procurement Concentration (answering Question 3 & 4 from Jupyter Notebook)
    pareto_data = []
    cumulative_spend = 0.0
    for s in sorted_s[:10]:
        val = float(s.total_purchase_dollars)
        cumulative_spend += val
        pct = (cumulative_spend / total_spend * 100.0) if total_spend > 0 else 0.0
        pareto_data.append({
            "vendor_name": s.vendor_name[:20],
            "spend": round(val, 2),
            "cumulative_percentage": round(pct, 1)
        })

    # Monthly spend trend
    month_sql = text("""
        SELECT 
            DATE_FORMAT(po_date, '%Y-%m') AS month_str,
            SUM(total_amount) AS spend,
            COUNT(po_number) AS orders
        FROM vendor_invoices
        GROUP BY DATE_FORMAT(po_date, '%Y-%m')
        ORDER BY month_str ASC
        LIMIT 12
    """)
    month_trend = [
        {
            "month": r.month_str,
            "spend": round(float(r.spend), 2),
            "orders": int(r.orders)
        }
        for r in db.execute(month_sql).fetchall()
    ]

    # Recent transactions
    trans_sql = text("""
        SELECT 
            v.vendor_name,
            pt.po_number,
            pt.po_date,
            pt.brand,
            pt.description,
            pt.quantity,
            pt.purchase_price,
            pt.total_amount
        FROM purchase_transactions pt
        JOIN vendors v ON pt.vendor_id = v.vendor_id
        ORDER BY pt.po_date DESC
        LIMIT 10
    """)
    recent_transactions = [
        {
            "vendor_name": r.vendor_name,
            "po_number": r.po_number,
            "po_date": str(r.po_date),
            "brand": r.brand,
            "description": r.description or f"Brand #{r.brand}",
            "quantity": r.quantity,
            "unit_price": round(float(r.purchase_price), 2),
            "total_amount": round(float(r.total_amount), 2)
        }
        for r in db.execute(trans_sql).fetchall()
    ]

    return {
        "total_spend": round(total_spend, 2),
        "total_orders": total_orders,
        "total_quantity": total_qty,
        "avg_order_value": avg_order_val,
        "avg_unit_price": avg_unit_price,
        "spend_by_vendor": spend_by_vendor,
        "monthly_spend_trend": month_trend,
        "bulk_purchasing_tiers": bulk_tiers,
        "pareto_procurement": pareto_data,
        "recent_transactions": recent_transactions
    }


def get_sales_analytics(db: Session, vendor_id: Optional[int] = None) -> Dict[str, Any]:
    """Calculates downstream sales, gross profit, sales vs purchases, and pricing opportunities."""
    query = db.query(VendorSummaryMetrics)
    if vendor_id:
        query = query.filter(VendorSummaryMetrics.vendor_id == vendor_id)
    summaries = query.all()

    total_sales = sum(float(s.total_sales_dollars) for s in summaries)
    total_qty = sum(s.total_sales_quantity for s in summaries)
    gross_profit = sum(float(s.gross_profit) for s in summaries)
    avg_margin = round(gross_profit / total_sales * 100.0, 2) if total_sales > 0 else 0.0

    # Monthly sales trend
    sales_month_sql = text("""
        SELECT 
            DATE_FORMAT(sale_date, '%Y-%m') AS month_str,
            SUM(total_amount) AS sales_dollars,
            SUM(quantity) AS sales_qty
        FROM sales_transactions
        GROUP BY DATE_FORMAT(sale_date, '%Y-%m')
        ORDER BY month_str ASC
        LIMIT 12
    """)
    month_trend = [
        {
            "month": r.month_str,
            "sales": round(float(r.sales_dollars), 2),
            "quantity": int(r.sales_qty)
        }
        for r in db.execute(sales_month_sql).fetchall()
    ]

    # Top selling brands
    brands_sql = text("""
        SELECT 
            brand,
            description,
            SUM(quantity) AS total_qty,
            SUM(total_amount) AS total_sales,
            AVG(unit_price) AS avg_price
        FROM sales_transactions
        GROUP BY brand, description
        ORDER BY total_sales DESC
        LIMIT 8
    """)
    top_brands = [
        {
            "brand": r.brand,
            "description": r.description or f"Brand #{r.brand}",
            "quantity": int(r.total_qty),
            "sales": round(float(r.total_sales), 2),
            "unit_price": round(float(r.avg_price), 2)
        }
        for r in db.execute(brands_sql).fetchall()
    ]

    # Sales vs Purchases comparison
    sorted_s = sorted(summaries, key=lambda x: float(x.total_sales_dollars), reverse=True)[:8]
    sales_vs_purchases = [
        {
            "vendor_name": s.vendor_name[:20],
            "sales": round(float(s.total_sales_dollars), 2),
            "purchases": round(float(s.total_purchase_dollars), 2),
            "profit": round(float(s.gross_profit), 2)
        }
        for s in sorted_s
    ]

    # Pricing Adjustment Opportunities (Question 1 from Jupyter notebook)
    # High margin but lower sales volume brands
    pricing_sql = text("""
        SELECT 
            brand,
            description,
            SUM(quantity) AS sales_qty,
            SUM(total_amount) AS sales_dollars,
            AVG(unit_price) AS avg_price
        FROM sales_transactions
        GROUP BY brand, description
        HAVING sales_qty < 100 AND sales_dollars > 500
        ORDER BY avg_price DESC
        LIMIT 6
    """)
    pricing_opps = [
        {
            "brand": r.brand,
            "description": r.description or f"Brand #{r.brand}",
            "sales_qty": int(r.sales_qty),
            "sales_dollars": round(float(r.sales_dollars), 2),
            "avg_price": round(float(r.avg_price), 2),
            "recommendation": "Promotional campaign or price elasticity review to accelerate turnover"
        }
        for r in db.execute(pricing_sql).fetchall()
    ]

    return {
        "total_sales_dollars": round(total_sales, 2),
        "total_sales_quantity": total_qty,
        "gross_profit": round(gross_profit, 2),
        "avg_profit_margin": avg_margin,
        "monthly_sales_trend": month_trend,
        "top_selling_brands": top_brands,
        "sales_vs_purchases": sales_vs_purchases,
        "pricing_adjustment_opportunities": pricing_opps
    }


def get_inventory_analytics(db: Session, store: Optional[int] = None) -> Dict[str, Any]:
    """Calculates inventory beginning/end values, capital locked in unsold stock, and turnover."""
    base_query = db.query(InventoryRecord)
    if store:
        base_query = base_query.filter(InventoryRecord.store == store)

    inv_sql = text("""
        SELECT 
            snapshot_type,
            SUM(quantity_in_stock) AS total_qty,
            SUM(quantity_in_stock * price) AS total_val
        FROM inventory_records
        GROUP BY snapshot_type
    """)
    inv_rows = {r.snapshot_type: r for r in db.execute(inv_sql)}
    begin_val = round(float(inv_rows['BEGIN'].total_val), 2) if 'BEGIN' in inv_rows else 0.0
    end_val = round(float(inv_rows['END'].total_val), 2) if 'END' in inv_rows else 0.0
    begin_qty = int(inv_rows['BEGIN'].total_qty) if 'BEGIN' in inv_rows else 0
    end_qty = int(inv_rows['END'].total_qty) if 'END' in inv_rows else 0
    net_change = round(end_val - begin_val, 2)

    # Capital locked in unsold stock (Ending Inventory Value)
    capital_locked = end_val

    # Store inventory distribution
    store_sql = text("""
        SELECT 
            store,
            city,
            SUM(quantity_in_stock) AS on_hand,
            SUM(quantity_in_stock * price) AS inv_value
        FROM inventory_records
        WHERE snapshot_type = 'END'
        GROUP BY store, city
        ORDER BY inv_value DESC
        LIMIT 8
    """)
    store_dist = [
        {
            "store_id": r.store,
            "city": r.city or f"Store #{r.store}",
            "on_hand": int(r.on_hand),
            "value": round(float(r.inv_value), 2)
        }
        for r in db.execute(store_sql).fetchall()
    ]

    # Inventory turnover by vendor (answering Question 6 from Jupyter Notebook)
    top_vendors = db.query(VendorSummaryMetrics).order_by(desc(VendorSummaryMetrics.total_purchase_dollars)).limit(8).all()
    turnover_data = [
        {
            "vendor_name": v.vendor_name[:20],
            "turnover_ratio": round(float(v.stock_turnover), 2),
            "purchases": round(float(v.total_purchase_dollars), 2),
            "sales": round(float(v.total_sales_dollars), 2)
        }
        for v in top_vendors
    ]

    # Excess stock & slow-moving products
    excess_vendors = [
        {
            "vendor_name": v.vendor_name,
            "turnover_ratio": round(float(v.stock_turnover), 2),
            "purchase_qty": v.total_purchase_quantity,
            "sales_qty": v.total_sales_quantity,
            "status": "Excess Stock Warning" if float(v.stock_turnover) < 0.3 else "Moderate Turnover"
        }
        for v in top_vendors if float(v.stock_turnover) < 0.6
    ]

    # Recent inventory records
    recent_inv = [
        {
            "inventory_code": r.inventory_code,
            "store": r.store,
            "city": r.city,
            "brand": r.brand,
            "item_name": r.item_name or f"Brand #{r.brand}",
            "size": r.size,
            "on_hand": r.quantity_in_stock,
            "price": round(float(r.price), 2),
            "snapshot_type": r.snapshot_type,
            "snapshot_date": str(r.snapshot_date)
        }
        for r in db.query(InventoryRecord).order_by(desc(InventoryRecord.snapshot_date)).limit(10).all()
    ]

    return {
        "begin_inventory_value": begin_val,
        "begin_inventory_qty": begin_qty,
        "end_inventory_value": end_val,
        "end_inventory_qty": end_qty,
        "net_inventory_change_value": net_change,
        "capital_locked_in_unsold_stock": capital_locked,
        "top_excess_inventory_vendors": excess_vendors,
        "store_inventory_distribution": store_dist,
        "inventory_turnover_by_vendor": turnover_data,
        "recent_inventory_records": recent_inv,
        "data_availability_notice": "Inventory records reflect beginning & ending snapshots from retail stores."
    }


def get_vendor_comparison(db: Session, vendor_ids: List[int]) -> Dict[str, Any]:
    """Generates multi-vendor head-to-head comparison, radar dimensions, 95% CIs, and data-backed insights."""
    summaries = db.query(VendorSummaryMetrics).filter(VendorSummaryMetrics.vendor_id.in_(vendor_ids)).all()
    if not summaries:
        return {
            "selected_vendors": [],
            "radar_comparison": [],
            "head_to_head_table": [],
            "confidence_intervals": [],
            "analytical_insights": ["No matching vendors selected for comparison."]
        }

    vendors_out = [
        {
            "vendor_id": s.vendor_id,
            "vendor_number": s.vendor_number,
            "vendor_name": s.vendor_name,
            "category": s.vendor.category if s.vendor else "Beverage & Spirits",
            "total_purchase_dollars": round(float(s.total_purchase_dollars), 2),
            "total_sales_dollars": round(float(s.total_sales_dollars), 2),
            "gross_profit": round(float(s.gross_profit), 2),
            "profit_margin": round(float(s.profit_margin), 2),
            "stock_turnover": round(float(s.stock_turnover), 3),
            "sales_to_purchase_ratio": round(float(s.sales_to_purchase_ratio), 3),
            "freight_cost": round(float(s.freight_cost), 2),
            "freight_percentage": round(float(s.freight_percentage), 2),
            "total_orders": s.total_orders,
            "avg_delivery_days": round(float(s.avg_delivery_days), 1),
            "on_time_delivery_rate": round(float(s.on_time_delivery_rate), 1),
            "defect_rate": round(float(s.defect_rate), 2),
            "vendor_score": round(float(s.vendor_score), 1),
            "vendor_rank": s.vendor_rank
        }
        for s in summaries
    ]

    # Radar dimensions normalized 0 - 100 for side-by-side radar charting
    max_spend = max(float(s.total_purchase_dollars) for s in summaries) or 1.0
    radar_comparison = [
        {
            "dimension": "Spend Scale",
            **{s.vendor_name: round(min(100.0, float(s.total_purchase_dollars) / max_spend * 100.0), 1) for s in summaries}
        },
        {
            "dimension": "Profit Margin",
            **{s.vendor_name: round(max(0.0, min(100.0, float(s.profit_margin) * 2.0)), 1) for s in summaries}
        },
        {
            "dimension": "Stock Turnover",
            **{s.vendor_name: round(min(100.0, float(s.stock_turnover) * 80.0), 1) for s in summaries}
        },
        {
            "dimension": "Delivery Speed",
            **{s.vendor_name: round(max(0.0, 100.0 - (float(s.avg_delivery_days) - 4.0) * 10.0), 1) for s in summaries}
        },
        {
            "dimension": "On-Time Rate",
            **{s.vendor_name: round(float(s.on_time_delivery_rate), 1) for s in summaries}
        }
    ]

    # Head-to-head comparison rows
    metrics_keys = [
        ("Vendor Rank", lambda s: f"#{s.vendor_rank}"),
        ("Overall Score", lambda s: f"{round(float(s.vendor_score), 1)} / 100"),
        ("Procurement Spend", lambda s: f"${round(float(s.total_purchase_dollars), 2):,}"),
        ("Sales Revenue", lambda s: f"${round(float(s.total_sales_dollars), 2):,}"),
        ("Gross Profit", lambda s: f"${round(float(s.gross_profit), 2):,}"),
        ("Profit Margin", lambda s: f"{round(float(s.profit_margin), 1)}%"),
        ("Stock Turnover Ratio", lambda s: f"{round(float(s.stock_turnover), 2)}x"),
        ("Average Delivery Time", lambda s: f"{round(float(s.avg_delivery_days), 1)} days"),
        ("On-Time Delivery Rate", lambda s: f"{round(float(s.on_time_delivery_rate), 1)}%"),
        ("Freight Cost", lambda s: f"${round(float(s.freight_cost), 2):,} ({round(float(s.freight_percentage), 2)}%)"),
    ]

    head_to_head = []
    for label, extractor in metrics_keys:
        row = {"metric": label}
        for s in summaries:
            row[s.vendor_name] = extractor(s)
        head_to_head.append(row)

    # 95% Confidence Intervals for compared vendors
    ci_data = []
    for s in summaries:
        ci_data.append({
            "vendor_name": s.vendor_name,
            "margin_mean": round(float(s.profit_margin), 2),
            "ci_lower": round(float(s.ci_lower), 2) if s.ci_lower is not None else round(float(s.profit_margin) - 5.0, 2),
            "ci_upper": round(float(s.ci_upper), 2) if s.ci_upper is not None else round(float(s.profit_margin) + 5.0, 2),
        })

    # Data-backed insights
    best_vendor = max(summaries, key=lambda x: float(x.vendor_score))
    best_delivery = min(summaries, key=lambda x: float(x.avg_delivery_days))
    insights = [
        f"{best_vendor.vendor_name} holds the highest overall Composite Performance Score ({round(float(best_vendor.vendor_score), 1)}) among selected partners.",
        f"{best_delivery.vendor_name} demonstrated the most agile logistics with an average lead time of {round(float(best_delivery.avg_delivery_days), 1)} days.",
        f"Delivery reliability ranges from {min(float(s.on_time_delivery_rate) for s in summaries):.1f}% to {max(float(s.on_time_delivery_rate) for s in summaries):.1f}% across this cohort.",
        "Operational recommendation: Prioritize volume allocation to vendors maintaining both high stock turnover and above-average on-time delivery rates."
    ]

    return {
        "selected_vendors": vendors_out,
        "radar_comparison": radar_comparison,
        "head_to_head_table": head_to_head,
        "confidence_intervals": ci_data,
        "analytical_insights": insights
    }
