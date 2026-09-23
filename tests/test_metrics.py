import pytest
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.metrics import (calculate_total_revenue, calculate_total_orders, calculate_unique_customers, calculate_repeat_customers, calculate_repeat_purchase_rate, calculate_aov, calculate_engagement_rate, calculate_overall_ctr, calculate_overall_conversion_rate)

def test_total_revenue():
    df = pd.DataFrame({'order_value': [100, 200, 300]})
    assert calculate_total_revenue(df) == 600.0

def test_total_revenue_empty():
    assert calculate_total_revenue(pd.DataFrame()) == 0.0

def test_total_orders():
    df = pd.DataFrame({'order_id': ['O1', 'O2', 'O3']})
    assert calculate_total_orders(df) == 3

def test_unique_customers():
    df = pd.DataFrame({'customer_id': ['C1', 'C1', 'C2']})
    assert calculate_unique_customers(df) == 2

def test_repeat_customers():
    df = pd.DataFrame({'customer_id': ['C1', 'C1', 'C2'], 'order_id': ['O1', 'O2', 'O3']})
    assert calculate_repeat_customers(df) == 1

def test_repeat_purchase_rate():
    df = pd.DataFrame({'customer_id': ['C1', 'C1', 'C2', 'C3'], 'order_id': ['O1', 'O2', 'O3', 'O4']})
    rate = calculate_repeat_purchase_rate(df)
    assert abs(rate - 33.33) < 1  # 1 repeat out of 3 customers

def test_aov():
    df = pd.DataFrame({'order_value': [100, 200, 300], 'order_id': ['O1', 'O2', 'O3']})
    assert calculate_aov(df) == 200.0

def test_engagement_rate():
    df = pd.DataFrame({'impressions': [1000], 'likes': [50], 'comments': [10], 'shares': [5], 'saves': [5]})
    rate = calculate_engagement_rate(df)
    assert abs(rate - 7.0) < 1e-9  # 70/1000*100

def test_ctr():
    df = pd.DataFrame({'impressions': [1000], 'referral_clicks': [50]})
    assert calculate_overall_ctr(df) == 5.0

def test_conversion_rate():
    campaigns = pd.DataFrame({'referral_clicks': [100]})
    purchases = pd.DataFrame({'order_id': ['O1', 'O2', 'O3']})
    rate = calculate_overall_conversion_rate(campaigns, purchases)
    assert rate == 3.0

def test_metrics_with_missing_columns():
    df = pd.DataFrame({'x': [1]})
    assert calculate_total_revenue(df) == 0.0
    assert calculate_unique_customers(df) == 0
    assert calculate_repeat_customers(df) == 0
    assert calculate_engagement_rate(df) == 0.0
