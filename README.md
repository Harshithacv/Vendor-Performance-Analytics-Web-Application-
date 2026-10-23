# Vendor Performance Analytics Web Application

A full-stack, data-driven web application for enterprise supply chain procurement and vendor performance analytics. Built using **React.js (JavaScript/JSX)**, **Tailwind CSS**, **Recharts**, **Python (FastAPI)**, **Pandas**, **SQLAlchemy**, and **MySQL 8.0**.

---

## 1. System Architecture & Data Pipeline

The application adheres strictly to the required multi-tier pipeline:

```
Original Dataset (c:\Users\91938\Downloads\venderdataset)
                      ↓
  Python / Pandas Cleaning & Ingestion Engine
                      ↓
           MySQL Relational Database
                      ↓
    Python Analytics & CVPI Scoring Engine
                      ↓
             FastAPI REST APIs
                      ↓
     React.js Dashboard & Visualization UI
```

---

## 2. Mandatory Technology Stack

| Tier | Technologies Used |
|---|---|
| **Frontend** | React 19, JavaScript (ES6+), JSX, Tailwind CSS v4, Recharts, Lucide Icons, React Router v7, Axios |
| **Backend** | Python 3.12, FastAPI, Pandas, NumPy, SciPy, SQLAlchemy 2.0, Pydantic v2, Uvicorn |
| **Database** | MySQL 8.0 Community Server, PyMySQL driver, SQL DDL Schema |
| **Testing** | Pytest (Backend API & analytics tests), Vitest & React Testing Library (Frontend UI tests) |

---

## 3. Database Schema Overview (`schema.sql`)

The MySQL database `vendor_analytics_db` includes the following 8 relational tables:

1. **`users`**: Authentication credentials, names, roles, and salted password hashes.
2. **`upload_batches`**: Audit tracking of file uploads, rows processed, and validation status.
3. **`vendors`**: Master vendor directory (vendor number, vendor name, category).
4. **`purchase_transactions`**: Granular purchase line items (PO number, PO date, receiving date, brand, unit price, quantity, dollars).
5. **`sales_transactions`**: Downstream retail sales orders (store, brand, sales date, quantity, total dollars, retail price).
6. **`inventory_records`**: Retail branch inventory snapshots (beginning vs ending stock on hand, unit prices, store locations).
7. **`vendor_invoices`**: Invoice-level aggregation tracking PO dates, invoice dates, total dollars, freight costs, and approvals.
8. **`vendor_summary_metrics`**: Analytical aggregate cache (procurement spend, downstream sales, gross profit, profit margin, stock turnover, lead time, on-time delivery rate, freight %, composite score, rank, 95% confidence intervals).

---

## 4. Analytical KPIs & Scoring Methodology

### A. Average Delivery Lead Time & On-Time Delivery Rate
* **Average Delivery Days**: `AVG(actual_delivery_date - po_date)` across delivered purchase orders.
* **On-Time Delivery Rate**: `(Delivered orders on or before expected SLA ÷ Total delivered orders) × 100`. (Empirical median SLA is benchmarked at 9 days).

### B. Commercial Margins & Velocity
* **Gross Profit**: `Total Sales Dollars - Total Purchase Dollars`.
* **Profit Margin (%)**: `(Gross Profit ÷ Total Sales Dollars) × 100`.
* **Stock Turnover Ratio**: `Total Sales Quantity ÷ Total Purchase Quantity`.
* **Freight Cost Efficiency**: `(Freight Cost ÷ Procurement Dollars) × 100`.

### C. Composite Vendor Performance Index (CVPI)
Every vendor receives an objective performance score on a **0 to 100 scale**:
$$\text{CVPI} = (0.20 \times \text{Spend Scale}) + (0.25 \times \text{Profit Margin}) + (0.25 \times \text{Stock Turnover}) + (0.20 \times \text{Delivery SLA}) + (0.10 \times \text{Freight Efficiency})$$
Vendors are ranked monotonically ($1 \dots N$) based on their CVPI score.

### D. 95% Confidence Intervals
Profit margins across vendor cohorts are evaluated with Student's $t$-distribution:
$$\text{CI}_{95\%} = \bar{x} \pm t_{0.025, n-1} \times \frac{s}{\sqrt{n}}$$

---

## 5. Quick Start Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- MySQL Server 8.0 running on `localhost:3306`

### Step 1: Database Setup
```bash
cd backend
mysql -u root -e "CREATE DATABASE IF NOT EXISTS vendor_analytics_db;"
mysql -u root vendor_analytics_db < schema.sql
```

### Step 2: Backend Setup & Seed Dataset
```bash
cd backend
pip install -r requirements.txt
python seed_data.py
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
* Backend API documentation available at: **http://127.0.0.1:8000/docs**
* Health check: **http://127.0.0.1:8000/api/health**

### Step 3: Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
* Web Dashboard available at: **http://127.0.0.1:5173/**

### Default Authentication Credentials
* **Email:** `admin@vendoranalytics.com`
* **Password:** `admin123`

---

## 6. Running Automated Tests

### Backend Unit & Integration Tests (Pytest)
```bash
cd backend
python -m pytest
```

### Frontend Tests (Vitest)
```bash
cd frontend
npx vitest run
```

---

## 7. Deliverables & Features Status

| Feature | Status | Notes |
|---|---|---|
| User Authentication | Complete | JWT tokens, salted hashing, protected routing, login & sign-up |
| Executive Dashboard | Complete | Live KPI cards, Recharts visualizations, quality notices |
| Vendor Directory & Scoring | Complete | Search, sorting, pagination, CVPI scoring and ranking |
| Vendor Detail Scorecard | Complete | PO history, monthly spend trends, top brands supplied |
| Purchase & Sales Analytics | Complete | Bulk order tiers, Pareto concentration, pricing opportunities |
| Inventory Analytics | Complete | Begin vs End stock, store valuation, capital locked in unsold stock |
| Vendor Comparison | Complete | 5-axis Radar chart, Head-to-head table, 95% CI margins, insights |
| Data Upload & Validation | Complete | 2-step drag-and-drop workflow, duplicate detection, cleaning pipeline |
| Filtered Reports Export | Complete | Real-time CSV generation matching active filters |
