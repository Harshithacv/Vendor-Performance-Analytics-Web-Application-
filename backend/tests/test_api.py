from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"

def test_dashboard_summary():
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "kpis" in data
    assert data["kpis"]["total_vendors"] > 0
    assert "top_vendors_by_spend" in data

def test_vendors_list():
    response = client.get("/api/vendors?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert "vendors" in data
    assert len(data["vendors"]) > 0
    assert data["total_count"] > 0
    first_vendor = data["vendors"][0]
    assert "vendor_name" in first_vendor
    assert "vendor_score" in first_vendor

def test_purchasing_analytics():
    response = client.get("/api/analytics/purchasing")
    assert response.status_code == 200
    data = response.json()
    assert data["total_spend"] > 0
    assert "bulk_purchasing_tiers" in data
    assert "pareto_procurement" in data

def test_sales_analytics():
    response = client.get("/api/analytics/sales")
    assert response.status_code == 200
    data = response.json()
    assert "monthly_sales_trend" in data
    assert "top_selling_brands" in data

def test_inventory_analytics():
    response = client.get("/api/analytics/inventory")
    assert response.status_code == 200
    data = response.json()
    assert "begin_inventory_value" in data
    assert "end_inventory_value" in data

def test_vendor_comparison():
    # First get 2 vendor IDs
    v_resp = client.get("/api/vendors?page=1&page_size=2")
    vendors = v_resp.json()["vendors"]
    assert len(vendors) >= 2
    v1_id = vendors[0]["vendor_id"]
    v2_id = vendors[1]["vendor_id"]

    resp = client.post("/api/analytics/vendor-comparison", json={"vendor_ids": [v1_id, v2_id]})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["selected_vendors"]) == 2
    assert "radar_comparison" in data
    assert "head_to_head_table" in data
    assert len(data["analytical_insights"]) > 0
