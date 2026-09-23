import pytest
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.validation import validate_schema, validate_referential_integrity, validate_business_rules, validate_date_ranges, validate_numeric_ranges

def test_validate_schema_pass():
    df = pd.DataFrame({'a': [1], 'b': [2]})
    assert validate_schema(df, ['a', 'b']) == True

def test_validate_schema_fail():
    df = pd.DataFrame({'a': [1]})
    assert validate_schema(df, ['a', 'b']) == False

def test_referential_integrity():
    data = {
        'creators': pd.DataFrame({'creator_id': ['C1', 'C2']}),
        'campaigns': pd.DataFrame({'campaign_id': ['CAM1'], 'creator_id': ['C1']}),
        'customers': pd.DataFrame({'customer_id': ['CUST1']}),
        'purchases': pd.DataFrame({'order_id': ['O1'], 'customer_id': ['CUST1'], 'campaign_id': ['CAM1']})
    }
    results = validate_referential_integrity(data)
    assert all(r['status'] for r in results)

def test_referential_integrity_fail():
    data = {
        'creators': pd.DataFrame({'creator_id': ['C1']}),
        'campaigns': pd.DataFrame({'campaign_id': ['CAM1'], 'creator_id': ['C999']})
    }
    results = validate_referential_integrity(data)
    assert not results[0]['status']

def test_business_rules_clicks_exceed_impressions():
    data = {
        'campaigns': pd.DataFrame({'impressions': [100], 'referral_clicks': [200], 'likes': [10], 'comments': [5], 'shares': [3], 'saves': [2]})
    }
    results = validate_business_rules(data)
    clicks_check = [r for r in results if 'Clicks' in r['check']][0]
    assert not clicks_check['status']

def test_validate_date_ranges():
    df = pd.DataFrame({'date': pd.to_datetime(['2026-01-01', '2026-06-01'])})
    result = validate_date_ranges(df, 'date')
    assert result['status'] == True

def test_validate_numeric_ranges():
    df = pd.DataFrame({'val': [5, 10, 15]})
    result = validate_numeric_ranges(df, 'val', 0, 20)
    assert result['status'] == True

def test_validate_numeric_out_of_range():
    df = pd.DataFrame({'val': [5, 10, 25]})
    result = validate_numeric_ranges(df, 'val', 0, 20)
    assert not result['status']
