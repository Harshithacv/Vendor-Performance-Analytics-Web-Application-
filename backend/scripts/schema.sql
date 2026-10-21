-- ============================================================================
-- Production MySQL DDL Schema: Vendor Performance & Procurement Analytics
-- Engine: InnoDB | Character Set: utf8mb4 | Collation: utf8mb4_unicode_ci
-- ============================================================================

CREATE DATABASE IF NOT EXISTS procurement_analytics
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE procurement_analytics;

-- ----------------------------------------------------------------------------
-- Drop existing tables in reverse dependency order
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS v_vendor_kpi_summary;
DROP TABLE IF EXISTS inventory_status;
DROP TABLE IF EXISTS purchase_orders;
DROP TABLE IF EXISTS vendors;

-- ----------------------------------------------------------------------------
-- 1. Vendors Master Table
-- ----------------------------------------------------------------------------
CREATE TABLE vendors (
    vendor_id VARCHAR(32) NOT NULL,
    vendor_name VARCHAR(255) NOT NULL,
    category ENUM('Raw Materials', 'Packaging', 'Electronics', 'Hardware') NOT NULL,
    tier ENUM('Tier 1', 'Tier 2') NOT NULL DEFAULT 'Tier 1',
    contact_person VARCHAR(128) NULL,
    email VARCHAR(255) NULL,
    phone VARCHAR(64) NULL,
    location VARCHAR(255) NULL,
    status ENUM('Top Performer', 'At Risk', 'Underperforming') NOT NULL DEFAULT 'Top Performer',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (vendor_id),
    INDEX idx_vendors_category (category),
    INDEX idx_vendors_status (status),
    INDEX idx_vendors_name (vendor_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 2. Purchase Orders Table
-- ----------------------------------------------------------------------------
CREATE TABLE purchase_orders (
    purchase_id VARCHAR(64) NOT NULL,
    vendor_id VARCHAR(32) NOT NULL,
    category ENUM('Raw Materials', 'Packaging', 'Electronics', 'Hardware') NOT NULL,
    purchase_date DATE NOT NULL,
    expected_delivery DATE NOT NULL,
    actual_delivery DATE NULL,
    quantity_ordered INT UNSIGNED NOT NULL,
    quantity_received INT UNSIGNED NOT NULL DEFAULT 0,
    unit_cost DECIMAL(12, 2) NOT NULL,
    total_spend DECIMAL(14, 2) NOT NULL,
    delivery_delay_days INT NULL COMMENT 'Negative = early, 0 = on time, positive = late',
    quality_score DECIMAL(3, 2) NULL COMMENT 'Dock inspection score out of 5.0',
    order_status ENUM('Delivered', 'In Transit', 'Delayed') NOT NULL DEFAULT 'In Transit',
    invoice_status ENUM('Paid', 'Approved', 'Pending Review') NOT NULL DEFAULT 'Pending Review',
    destination_warehouse VARCHAR(128) NOT NULL DEFAULT 'Central DC - Chicago',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (purchase_id),
    CONSTRAINT fk_po_vendor
        FOREIGN KEY (vendor_id) REFERENCES vendors (vendor_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    INDEX idx_po_vendor_id (vendor_id),
    INDEX idx_po_dates (purchase_date, expected_delivery),
    INDEX idx_po_status (order_status),
    INDEX idx_po_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 3. Inventory Status & Movement Table
-- ----------------------------------------------------------------------------
CREATE TABLE inventory_status (
    sku VARCHAR(64) NOT NULL,
    item_name VARCHAR(255) NOT NULL,
    vendor_id VARCHAR(32) NOT NULL,
    category ENUM('Raw Materials', 'Packaging', 'Electronics', 'Hardware') NOT NULL,
    stock_on_hand INT UNSIGNED NOT NULL DEFAULT 0,
    reorder_level INT UNSIGNED NOT NULL DEFAULT 0,
    max_stock_level INT UNSIGNED NOT NULL DEFAULT 0,
    safety_stock INT UNSIGNED NOT NULL DEFAULT 0,
    unit_measure VARCHAR(32) NOT NULL DEFAULT 'pcs',
    unit_cost DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    total_valuation DECIMAL(14, 2) GENERATED ALWAYS AS (stock_on_hand * unit_cost) STORED,
    stock_status ENUM('Optimal', 'Reorder Warning', 'Slow-Moving', 'Critical Shortage') NOT NULL DEFAULT 'Optimal',
    warehouse_location VARCHAR(128) NOT NULL,
    last_restock_date DATE NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (sku),
    CONSTRAINT fk_inventory_vendor
        FOREIGN KEY (vendor_id) REFERENCES vendors (vendor_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    INDEX idx_inv_vendor_id (vendor_id),
    INDEX idx_inv_category (category),
    INDEX idx_inv_stock_status (stock_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 4. Analytical View: Real-Time Vendor KPI Performance
-- ----------------------------------------------------------------------------
CREATE VIEW v_vendor_kpi_summary AS
SELECT 
    v.vendor_id,
    v.vendor_name,
    v.category,
    v.tier,
    v.status AS recorded_status,
    COUNT(po.purchase_id) AS total_orders_placed,
    COALESCE(SUM(po.total_spend), 0.00) AS total_expenditure_ytd,
    COALESCE(SUM(CASE WHEN po.order_status = 'Delivered' THEN 1 ELSE 0 END), 0) AS orders_delivered,
    COALESCE(SUM(CASE WHEN po.order_status = 'Delivered' AND po.delivery_delay_days <= 0 THEN 1 ELSE 0 END), 0) AS orders_on_time,
    ROUND(
        (COALESCE(SUM(CASE WHEN po.order_status = 'Delivered' AND po.delivery_delay_days <= 0 THEN 1 ELSE 0 END), 0) /
        NULLIF(SUM(CASE WHEN po.order_status = 'Delivered' THEN 1 ELSE 0 END), 0)) * 100, 
        2
    ) AS otdr_percentage,
    ROUND(AVG(CASE WHEN po.order_status = 'Delivered' THEN po.quality_score ELSE NULL END), 2) AS avg_quality_rating,
    ROUND(
        (COALESCE(SUM(po.quantity_received), 0) / NULLIF(SUM(po.quantity_ordered), 0)) * 100,
        2
    ) AS order_fulfillment_rate
FROM vendors v
LEFT JOIN purchase_orders po ON v.vendor_id = po.vendor_id
GROUP BY v.vendor_id, v.vendor_name, v.category, v.tier, v.status;
