import numpy as np
import scipy.stats as stats
from typing import List, Dict, Any, Tuple

def calculate_confidence_interval(data: List[float], confidence: float = 0.95) -> Tuple[float, float, float]:
    """
    Calculates the 95% confidence interval for a list of values using Student's t-distribution.
    Returns (mean, lower_bound, upper_bound).
    """
    clean_data = [x for x in data if x is not None and not np.isnan(x)]
    n = len(clean_data)
    if n < 2:
        val = clean_data[0] if clean_data else 0.0
        return float(val), float(val), float(val)

    mean_val = float(np.mean(clean_data))
    std_err = float(stats.sem(clean_data))
    if std_err == 0:
        return mean_val, mean_val, mean_val

    h = std_err * stats.t.ppf((1 + confidence) / 2.0, n - 1)
    return round(mean_val, 2), round(mean_val - h, 2), round(mean_val + h, 2)

def calculate_vendor_composite_score(
    spend: float,
    max_spend: float,
    profit_margin: float,
    stock_turnover: float,
    avg_delivery_days: float,
    on_time_rate: float,
    freight_percentage: float
) -> float:
    """
    Calculates the Composite Vendor Performance Index (CVPI) on a 0 - 100 scale.
    
    Weights:
    - Commercial Spend & Volume (SVS): 20%
    - Profit Margin (PMS): 25%
    - Stock Turnover (STS): 25%
    - Delivery Performance (DPS): 20%
    - Freight Cost Efficiency (FES): 10%
    """
    # 1. Spend Volume Score (0-100)
    svs = min(100.0, (spend / max(1.0, max_spend)) * 100.0) if max_spend > 0 else 50.0

    # 2. Profit Margin Score (0-100). Baseline 30% margin is 75 score.
    # Normal industry beverage profit margins range between 10% and 50%.
    pms = max(0.0, min(100.0, profit_margin * 2.0))

    # 3. Stock Turnover Score (0-100). Ratio of sales to purchases.
    # Turnover ratio of 1.0 = 80 score, 1.2+ = 100 score.
    sts = min(100.0, stock_turnover * 80.0)

    # 4. Delivery Performance Score (0-100)
    # Average delivery days in dataset is ~9 days. Lower is better.
    # Baseline expected lead time is 7-10 days.
    delivery_speed_score = max(0.0, min(100.0, 100.0 - (max(0.0, avg_delivery_days - 5.0) * 8.0)))
    dps = (on_time_rate * 0.6) + (delivery_speed_score * 0.4)

    # 5. Freight Efficiency Score (0-100)
    # Freight is usually 0.5% to 2% of total dollars.
    # A freight percentage under 1% scores 90+, while > 3% reduces score.
    fes = max(0.0, min(100.0, 100.0 - (freight_percentage * 20.0)))

    # Weighted Composite Score
    composite_score = (
        (svs * 0.20) +
        (pms * 0.25) +
        (sts * 0.25) +
        (dps * 0.20) +
        (fes * 0.10)
    )

    return round(max(0.0, min(100.0, composite_score)), 2)
