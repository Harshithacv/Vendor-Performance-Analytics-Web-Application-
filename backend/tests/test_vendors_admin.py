import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import create_access_token

client = TestClient(app)

def test_authenticated_user_can_add_vendor():
    # 1. Generate authenticated user token
    user_token = create_access_token({"sub": "admin@vendoranalytics.com"})
    headers = {"Authorization": f"Bearer {user_token}"}

    # Get initial total vendors from dashboard summary
    dash_res_before = client.get("/api/dashboard/summary")
    initial_count = dash_res_before.json()["kpis"]["total_vendors"]

    # Use a unique vendor number
    unique_vendor_num = 999101
    payload = {
        "vendor_number": unique_vendor_num,
        "vendor_name": "Apex Spirits Distributing Co.",
        "category": "Spirits & Hard Liquor"
    }

    # Add vendor as authenticated user
    response = client.post("/api/vendors", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["vendor_number"] == unique_vendor_num
    assert data["vendor_name"] == "Apex Spirits Distributing Co."
    assert "successfully added" in data["message"]
    assert data["total_vendors_count"] == initial_count + 1

    # Verify dashboard total vendor count updated from MySQL
    dash_res_after = client.get("/api/dashboard/summary")
    new_count = dash_res_after.json()["kpis"]["total_vendors"]
    assert new_count == initial_count + 1

def test_unified_access_without_role_rejection():
    # 2. Verify any authenticated user has unified access without 403 role errors
    user_token = create_access_token({"sub": "shashankparutagoudra4@gmail.com"})
    headers = {"Authorization": f"Bearer {user_token}"}

    payload = {
        "vendor_number": 999102,
        "vendor_name": "Standard Distributing Corp",
        "category": "Wine & Champagne"
    }

    response = client.post("/api/vendors", json=payload, headers=headers)
    assert response.status_code == 201

def test_unauthenticated_cannot_add_vendor():
    # 3. No token
    payload = {
        "vendor_number": 999003,
        "vendor_name": "No Auth Vendor Inc"
    }
    response = client.post("/api/vendors", json=payload)
    assert response.status_code == 401

def test_duplicate_vendor_number_rejected():
    # 4. Duplicate number with auth token
    user_token = create_access_token({"sub": "admin@vendoranalytics.com"})
    headers = {"Authorization": f"Bearer {user_token}"}

    payload = {
        "vendor_number": 999101,  # Already created above
        "vendor_name": "Duplicate Vendor Test"
    }
    response = client.post("/api/vendors", json=payload, headers=headers)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]
