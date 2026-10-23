from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Numeric, Date, DateTime, 
    ForeignKey, Text, JSON, Enum
)
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="analyst", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    uploads = relationship("UploadBatch", back_populates="user")


class UploadBatch(Base):
    __tablename__ = "upload_batches"

    upload_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    row_count = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="completed", nullable=False)
    validation_summary = Column(JSON, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="uploads")
    purchases = relationship("PurchaseTransaction", back_populates="upload")
    sales = relationship("SalesTransaction", back_populates="upload")
    inventory = relationship("InventoryRecord", back_populates="upload")
    invoices = relationship("VendorInvoice", back_populates="upload")


class Vendor(Base):
    __tablename__ = "vendors"

    vendor_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    vendor_number = Column(Integer, unique=True, index=True, nullable=False)
    vendor_name = Column(String(255), index=True, nullable=False)
    category = Column(String(100), default="Beverage & Spirits", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    purchases = relationship("PurchaseTransaction", back_populates="vendor", cascade="all, delete")
    sales = relationship("SalesTransaction", back_populates="vendor")
    inventory = relationship("InventoryRecord", back_populates="vendor")
    invoices = relationship("VendorInvoice", back_populates="vendor", cascade="all, delete")
    summary = relationship("VendorSummaryMetrics", back_populates="vendor", uselist=False, cascade="all, delete")


class PurchaseTransaction(Base):
    __tablename__ = "purchase_transactions"

    purchase_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    vendor_id = Column(Integer, ForeignKey("vendors.vendor_id", ondelete="CASCADE"), nullable=False, index=True)
    upload_id = Column(Integer, ForeignKey("upload_batches.upload_id", ondelete="SET NULL"), nullable=True)
    po_number = Column(Integer, index=True, nullable=False)
    po_date = Column(Date, index=True, nullable=False)
    expected_delivery_date = Column(Date, nullable=True)
    actual_delivery_date = Column(Date, index=True, nullable=True)
    invoice_date = Column(Date, nullable=True)
    pay_date = Column(Date, nullable=True)
    store = Column(Integer, nullable=True)
    brand = Column(Integer, index=True, nullable=False)
    description = Column(String(255), nullable=True)
    size = Column(String(100), nullable=True)
    purchase_price = Column(Numeric(12, 2), default=0.00, nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    total_amount = Column(Numeric(14, 2), default=0.00, nullable=False)
    classification = Column(Integer, default=1, nullable=False)
    defect_quantity = Column(Integer, default=0, nullable=False)

    vendor = relationship("Vendor", back_populates="purchases")
    upload = relationship("UploadBatch", back_populates="purchases")


class SalesTransaction(Base):
    __tablename__ = "sales_transactions"

    sale_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    vendor_id = Column(Integer, ForeignKey("vendors.vendor_id", ondelete="SET NULL"), nullable=True, index=True)
    upload_id = Column(Integer, ForeignKey("upload_batches.upload_id", ondelete="SET NULL"), nullable=True)
    store = Column(Integer, nullable=False)
    brand = Column(Integer, index=True, nullable=False)
    description = Column(String(255), nullable=True)
    size = Column(String(100), nullable=True)
    sale_date = Column(Date, index=True, nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    total_amount = Column(Numeric(14, 2), default=0.00, nullable=False)
    unit_price = Column(Numeric(12, 2), default=0.00, nullable=False)
    volume = Column(Numeric(10, 2), nullable=True)
    excise_tax = Column(Numeric(12, 2), default=0.00, nullable=False)

    vendor = relationship("Vendor", back_populates="sales")
    upload = relationship("UploadBatch", back_populates="sales")


class InventoryRecord(Base):
    __tablename__ = "inventory_records"

    inventory_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    inventory_code = Column(String(150), nullable=True)
    vendor_id = Column(Integer, ForeignKey("vendors.vendor_id", ondelete="SET NULL"), nullable=True, index=True)
    upload_id = Column(Integer, ForeignKey("upload_batches.upload_id", ondelete="SET NULL"), nullable=True)
    store = Column(Integer, nullable=False)
    city = Column(String(150), nullable=True)
    brand = Column(Integer, index=True, nullable=False)
    item_name = Column(String(255), nullable=True)
    size = Column(String(100), nullable=True)
    quantity_in_stock = Column(Integer, default=0, nullable=False)
    price = Column(Numeric(12, 2), default=0.00, nullable=False)
    snapshot_type = Column(Enum("BEGIN", "END"), nullable=False, index=True)
    snapshot_date = Column(Date, nullable=False, index=True)

    vendor = relationship("Vendor", back_populates="inventory")
    upload = relationship("UploadBatch", back_populates="inventory")


class VendorInvoice(Base):
    __tablename__ = "vendor_invoices"

    invoice_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    vendor_id = Column(Integer, ForeignKey("vendors.vendor_id", ondelete="CASCADE"), nullable=False, index=True)
    upload_id = Column(Integer, ForeignKey("upload_batches.upload_id", ondelete="SET NULL"), nullable=True)
    po_number = Column(Integer, index=True, nullable=False)
    po_date = Column(Date, nullable=False)
    invoice_date = Column(Date, nullable=False)
    pay_date = Column(Date, nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    total_amount = Column(Numeric(14, 2), default=0.00, nullable=False)
    freight = Column(Numeric(12, 2), default=0.00, nullable=False)
    approval = Column(String(100), nullable=True)

    vendor = relationship("Vendor", back_populates="invoices")
    upload = relationship("UploadBatch", back_populates="invoices")


class VendorSummaryMetrics(Base):
    __tablename__ = "vendor_summary_metrics"

    summary_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    vendor_id = Column(Integer, ForeignKey("vendors.vendor_id", ondelete="CASCADE"), unique=True, nullable=False)
    vendor_number = Column(Integer, nullable=False)
    vendor_name = Column(String(255), nullable=False)
    total_purchase_dollars = Column(Numeric(16, 2), default=0.00, nullable=False)
    total_purchase_quantity = Column(Integer, default=0, nullable=False)
    total_sales_dollars = Column(Numeric(16, 2), default=0.00, nullable=False)
    total_sales_quantity = Column(Integer, default=0, nullable=False)
    gross_profit = Column(Numeric(16, 2), default=0.00, nullable=False)
    profit_margin = Column(Numeric(8, 2), default=0.00, nullable=False)
    stock_turnover = Column(Numeric(8, 3), default=0.00, nullable=False)
    sales_to_purchase_ratio = Column(Numeric(8, 3), default=0.00, nullable=False)
    freight_cost = Column(Numeric(14, 2), default=0.00, nullable=False)
    freight_percentage = Column(Numeric(8, 2), default=0.00, nullable=False)
    total_orders = Column(Integer, default=0, nullable=False)
    avg_delivery_days = Column(Numeric(8, 2), default=0.00, nullable=False)
    on_time_delivery_rate = Column(Numeric(8, 2), default=0.00, nullable=False)
    defect_rate = Column(Numeric(8, 2), default=0.00, nullable=False)
    vendor_score = Column(Numeric(8, 2), default=0.00, nullable=False)
    vendor_rank = Column(Integer, default=0, nullable=False)
    ci_lower = Column(Numeric(8, 2), nullable=True)
    ci_upper = Column(Numeric(8, 2), nullable=True)
    last_calculated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    vendor = relationship("Vendor", back_populates="summary")
