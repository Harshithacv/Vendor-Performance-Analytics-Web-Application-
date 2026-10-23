-- =============================================================================
-- VENDOR PERFORMANCE ANALYTICS DATABASE SCHEMA
-- Target Database: MySQL 8.0+
-- Character Set: utf8mb4 / Collation: utf8mb4_unicode_ci
-- =============================================================================

CREATE DATABASE IF NOT EXISTS `vendor_analytics_db` 
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE `vendor_analytics_db`;

-- 1. USERS TABLE (Authentication & Role Management)
CREATE TABLE IF NOT EXISTS `users` (
    `user_id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(150) NOT NULL,
    `email` VARCHAR(255) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `role` VARCHAR(50) NOT NULL DEFAULT 'analyst',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_users_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. UPLOAD_BATCHES TABLE (Dataset Upload Audit & Validation History)
CREATE TABLE IF NOT EXISTS `upload_batches` (
    `upload_id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NULL,
    `file_name` VARCHAR(255) NOT NULL,
    `file_type` VARCHAR(50) NOT NULL,
    `row_count` INT NOT NULL DEFAULT 0,
    `status` VARCHAR(50) NOT NULL DEFAULT 'completed',
    `validation_summary` JSON NULL,
    `uploaded_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_batches_user` FOREIGN KEY (`user_id`) 
        REFERENCES `users` (`user_id`) ON DELETE SET NULL,
    INDEX `idx_batches_status` (`status`),
    INDEX `idx_batches_date` (`uploaded_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. VENDORS TABLE (Master Vendor Directory)
CREATE TABLE IF NOT EXISTS `vendors` (
    `vendor_id` INT AUTO_INCREMENT PRIMARY KEY,
    `vendor_number` INT NOT NULL UNIQUE,
    `vendor_name` VARCHAR(255) NOT NULL,
    `category` VARCHAR(100) NOT NULL DEFAULT 'Beverage & Spirits',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_vendors_number` (`vendor_number`),
    INDEX `idx_vendors_name` (`vendor_name`),
    INDEX `idx_vendors_category` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. PURCHASE_TRANSACTIONS TABLE (Procurement Orders & Deliveries)
CREATE TABLE IF NOT EXISTS `purchase_transactions` (
    `purchase_id` INT AUTO_INCREMENT PRIMARY KEY,
    `vendor_id` INT NOT NULL,
    `upload_id` INT NULL,
    `po_number` INT NOT NULL,
    `po_date` DATE NOT NULL,
    `expected_delivery_date` DATE NULL,
    `actual_delivery_date` DATE NULL,
    `invoice_date` DATE NULL,
    `pay_date` DATE NULL,
    `store` INT NULL,
    `brand` INT NOT NULL,
    `description` VARCHAR(255) NULL,
    `size` VARCHAR(100) NULL,
    `purchase_price` DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    `quantity` INT NOT NULL DEFAULT 0,
    `total_amount` DECIMAL(14, 2) NOT NULL DEFAULT 0.00,
    `classification` INT NOT NULL DEFAULT 1,
    `defect_quantity` INT NOT NULL DEFAULT 0,
    CONSTRAINT `fk_purchases_vendor` FOREIGN KEY (`vendor_id`) 
        REFERENCES `vendors` (`vendor_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_purchases_upload` FOREIGN KEY (`upload_id`) 
        REFERENCES `upload_batches` (`upload_id`) ON DELETE SET NULL,
    INDEX `idx_purchases_vendor_id` (`vendor_id`),
    INDEX `idx_purchases_po` (`po_number`),
    INDEX `idx_purchases_brand` (`brand`),
    INDEX `idx_purchases_po_date` (`po_date`),
    INDEX `idx_purchases_receiving_date` (`actual_delivery_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. SALES_TRANSACTIONS TABLE (Downstream Sales & Outflow)
CREATE TABLE IF NOT EXISTS `sales_transactions` (
    `sale_id` INT AUTO_INCREMENT PRIMARY KEY,
    `vendor_id` INT NULL,
    `upload_id` INT NULL,
    `store` INT NOT NULL,
    `brand` INT NOT NULL,
    `description` VARCHAR(255) NULL,
    `size` VARCHAR(100) NULL,
    `sale_date` DATE NOT NULL,
    `quantity` INT NOT NULL DEFAULT 0,
    `total_amount` DECIMAL(14, 2) NOT NULL DEFAULT 0.00,
    `unit_price` DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    `volume` DECIMAL(10, 2) NULL,
    `excise_tax` DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    CONSTRAINT `fk_sales_vendor` FOREIGN KEY (`vendor_id`) 
        REFERENCES `vendors` (`vendor_id`) ON DELETE SET NULL,
    CONSTRAINT `fk_sales_upload` FOREIGN KEY (`upload_id`) 
        REFERENCES `upload_batches` (`upload_id`) ON DELETE SET NULL,
    INDEX `idx_sales_vendor_id` (`vendor_id`),
    INDEX `idx_sales_brand` (`brand`),
    INDEX `idx_sales_date` (`sale_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. INVENTORY_RECORDS TABLE (Beginning & Ending Stock Snapshots)
CREATE TABLE IF NOT EXISTS `inventory_records` (
    `inventory_id` INT AUTO_INCREMENT PRIMARY KEY,
    `inventory_code` VARCHAR(150) NULL,
    `vendor_id` INT NULL,
    `upload_id` INT NULL,
    `store` INT NOT NULL,
    `city` VARCHAR(150) NULL,
    `brand` INT NOT NULL,
    `item_name` VARCHAR(255) NULL,
    `size` VARCHAR(100) NULL,
    `quantity_in_stock` INT NOT NULL DEFAULT 0,
    `price` DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    `snapshot_type` ENUM('BEGIN', 'END') NOT NULL,
    `snapshot_date` DATE NOT NULL,
    CONSTRAINT `fk_inventory_vendor` FOREIGN KEY (`vendor_id`) 
        REFERENCES `vendors` (`vendor_id`) ON DELETE SET NULL,
    CONSTRAINT `fk_inventory_upload` FOREIGN KEY (`upload_id`) 
        REFERENCES `upload_batches` (`upload_id`) ON DELETE SET NULL,
    INDEX `idx_inventory_vendor_id` (`vendor_id`),
    INDEX `idx_inventory_brand` (`brand`),
    INDEX `idx_inventory_type` (`snapshot_type`),
    INDEX `idx_inventory_date` (`snapshot_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. VENDOR_INVOICES TABLE (Invoice Level Freight & Approval Summary)
CREATE TABLE IF NOT EXISTS `vendor_invoices` (
    `invoice_id` INT AUTO_INCREMENT PRIMARY KEY,
    `vendor_id` INT NOT NULL,
    `upload_id` INT NULL,
    `po_number` INT NOT NULL,
    `po_date` DATE NOT NULL,
    `invoice_date` DATE NOT NULL,
    `pay_date` DATE NOT NULL,
    `quantity` INT NOT NULL DEFAULT 0,
    `total_amount` DECIMAL(14, 2) NOT NULL DEFAULT 0.00,
    `freight` DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    `approval` VARCHAR(100) NULL,
    CONSTRAINT `fk_invoices_vendor` FOREIGN KEY (`vendor_id`) 
        REFERENCES `vendors` (`vendor_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_invoices_upload` FOREIGN KEY (`upload_id`) 
        REFERENCES `upload_batches` (`upload_id`) ON DELETE SET NULL,
    INDEX `idx_invoices_vendor_id` (`vendor_id`),
    INDEX `idx_invoices_po` (`po_number`),
    INDEX `idx_invoices_dates` (`po_date`, `invoice_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. VENDOR_SUMMARY_METRICS TABLE (Precomputed / Cached Performance Aggregates)
CREATE TABLE IF NOT EXISTS `vendor_summary_metrics` (
    `summary_id` INT AUTO_INCREMENT PRIMARY KEY,
    `vendor_id` INT NOT NULL UNIQUE,
    `vendor_number` INT NOT NULL,
    `vendor_name` VARCHAR(255) NOT NULL,
    `total_purchase_dollars` DECIMAL(16, 2) NOT NULL DEFAULT 0.00,
    `total_purchase_quantity` INT NOT NULL DEFAULT 0,
    `total_sales_dollars` DECIMAL(16, 2) NOT NULL DEFAULT 0.00,
    `total_sales_quantity` INT NOT NULL DEFAULT 0,
    `gross_profit` DECIMAL(16, 2) NOT NULL DEFAULT 0.00,
    `profit_margin` DECIMAL(8, 2) NOT NULL DEFAULT 0.00,
    `stock_turnover` DECIMAL(8, 3) NOT NULL DEFAULT 0.00,
    `sales_to_purchase_ratio` DECIMAL(8, 3) NOT NULL DEFAULT 0.00,
    `freight_cost` DECIMAL(14, 2) NOT NULL DEFAULT 0.00,
    `freight_percentage` DECIMAL(8, 2) NOT NULL DEFAULT 0.00,
    `total_orders` INT NOT NULL DEFAULT 0,
    `avg_delivery_days` DECIMAL(8, 2) NOT NULL DEFAULT 0.00,
    `on_time_delivery_rate` DECIMAL(8, 2) NOT NULL DEFAULT 0.00,
    `defect_rate` DECIMAL(8, 2) NOT NULL DEFAULT 0.00,
    `vendor_score` DECIMAL(8, 2) NOT NULL DEFAULT 0.00,
    `vendor_rank` INT NOT NULL DEFAULT 0,
    `ci_lower` DECIMAL(8, 2) NULL,
    `ci_upper` DECIMAL(8, 2) NULL,
    `last_calculated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_summary_vendor` FOREIGN KEY (`vendor_id`) 
        REFERENCES `vendors` (`vendor_id`) ON DELETE CASCADE,
    INDEX `idx_summary_score` (`vendor_score`),
    INDEX `idx_summary_rank` (`vendor_rank`),
    INDEX `idx_summary_spend` (`total_purchase_dollars`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
