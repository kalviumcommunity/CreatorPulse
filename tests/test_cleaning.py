import pytest
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.cleaning import clean_creators, clean_campaigns, clean_purchases, detect_duplicates, remove_duplicates, handle_missing_values

def test_clean_creators_normalizes_names():
    df = pd.DataFrame({'creator_id': ['C1'], 'creator_name': ['  john DOE  '], 'followers': [1000], 'creator_category': ['tech']})
    result = clean_creators(df)
    assert result['creator_name'].iloc[0] == 'John Doe'

def test_clean_creators_handles_negative_followers():
    df = pd.DataFrame({'creator_id': ['C1'], 'creator_name': ['Test'], 'followers': [-100], 'creator_category': ['tech']})
    result = clean_creators(df)
    assert result['followers'].iloc[0] == 0

def test_clean_campaigns_parses_budget():
    df = pd.DataFrame({'campaign_id': ['CAM1'], 'campaign_budget': ['₹10,000'], 'campaign_start_date': ['2026-01-01'], 'campaign_end_date': ['2026-01-15'], 'content_type': ['review'], 'platform': ['instagram']})
    result = clean_campaigns(df)
    assert result['campaign_budget'].iloc[0] == 10000.0

def test_clean_purchases_flags_refunds():
    df = pd.DataFrame({'order_id': ['O1', 'O2'], 'purchase_date': ['2026-01-01', '2026-01-02'], 'order_value': [500, -200]})
    result = clean_purchases(df)
    assert result['is_refund'].iloc[0] == False
    assert result['is_refund'].iloc[1] == True

def test_detect_duplicates():
    df = pd.DataFrame({'a': [1, 1, 2], 'b': [3, 3, 4]})
    result = detect_duplicates(df)
    assert result['duplicate_rows'] == 1

def test_remove_duplicates():
    df = pd.DataFrame({'a': [1, 1, 2], 'b': [3, 3, 4]})
    result = remove_duplicates(df)
    assert len(result) == 2

def test_handle_missing_mean():
    df = pd.DataFrame({'a': [1, None, 3]})
    result = handle_missing_values(df, {'a': 'mean'})
    assert result['a'].iloc[1] == 2.0

def test_empty_dataframe():
    df = pd.DataFrame()
    assert clean_creators(df).empty
    assert clean_campaigns(df).empty
    assert clean_purchases(df).empty
