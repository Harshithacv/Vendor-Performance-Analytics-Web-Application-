import pytest
from app.services.vendor_scoring import calculate_confidence_interval, calculate_vendor_composite_score

def test_confidence_interval_basic():
    data = [20.0, 22.0, 19.0, 24.0, 21.0, 23.0]
    mean, lower, upper = calculate_confidence_interval(data, confidence=0.95)
    assert round(mean, 1) == 21.5
    assert lower < mean < upper
    assert round(lower, 1) > 19.0

def test_confidence_interval_single_value():
    mean, lower, upper = calculate_confidence_interval([15.5])
    assert mean == 15.5
    assert lower == 15.5
    assert upper == 15.5

def test_composite_score_bounds():
    # Maximum high performer
    score_high = calculate_vendor_composite_score(
        spend=1000000,
        max_spend=1000000,
        profit_margin=45.0,
        stock_turnover=1.5,
        avg_delivery_days=5.0,
        on_time_rate=99.0,
        freight_percentage=0.5
    )
    assert 70.0 <= score_high <= 100.0

    # Minimum low performer
    score_low = calculate_vendor_composite_score(
        spend=100,
        max_spend=1000000,
        profit_margin=-10.0,
        stock_turnover=0.05,
        avg_delivery_days=25.0,
        on_time_rate=20.0,
        freight_percentage=15.0
    )
    assert 0.0 <= score_low <= 30.0
