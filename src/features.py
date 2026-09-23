import pandas as pd
from typing import Dict, Any
from .utils import safe_divide

def add_engagement_rate(df: pd.DataFrame) -> pd.DataFrame:
    """(likes+comments+shares+saves)/impressions*100"""
    if df.empty:
        return df
    df = df.copy()
    eng_cols = ['likes', 'comments', 'shares', 'saves']
    if 'impressions' in df.columns and all(c in df.columns for c in eng_cols):
        df['total_engagement'] = df[eng_cols].sum(axis=1)
        df['engagement_rate'] = df.apply(lambda row: safe_divide(row['total_engagement'], row['impressions']) * 100, axis=1)
    return df

def add_ctr(df: pd.DataFrame) -> pd.DataFrame:
    """referral_clicks/impressions*100"""
    if df.empty:
        return df
    df = df.copy()
    if 'impressions' in df.columns and 'referral_clicks' in df.columns:
        df['ctr'] = df.apply(lambda row: safe_divide(row['referral_clicks'], row['impressions']) * 100, axis=1)
    return df

def add_conversion_rate(df: pd.DataFrame, purchases_df: pd.DataFrame) -> pd.DataFrame:
    """purchases/referral_clicks*100 per campaign"""
    if df.empty:
        return df
    df = df.copy()
    if 'campaign_id' in df.columns and 'campaign_id' in purchases_df.columns:
        # Avoid counting refunds as conversions if desired, but for now count total orders
        orders_per_camp = purchases_df.groupby('campaign_id').size().reset_index(name='purchases')
        df = df.merge(orders_per_camp, on='campaign_id', how='left')
        df['purchases'] = df['purchases'].fillna(0)
        if 'referral_clicks' in df.columns:
            df['conversion_rate'] = df.apply(lambda row: safe_divide(row['purchases'], row['referral_clicks']) * 100, axis=1)
    return df

def add_creator_tier(df: pd.DataFrame) -> pd.DataFrame:
    """Based on follower thresholds."""
    if df.empty:
        return df
    df = df.copy()
    if 'followers' in df.columns:
        def get_tier(f):
            if f > 1000000: return 'Mega'
            elif f >= 500000: return 'Macro'
            elif f >= 100000: return 'Mid-Tier'
            elif f >= 10000: return 'Micro'
            else: return 'Nano'
        df['creator_tier'] = df['followers'].apply(get_tier)
    return df

def add_customer_segments(customers_df: pd.DataFrame, purchases_df: pd.DataFrame) -> pd.DataFrame:
    """One-time/Repeat/High-value"""
    if customers_df.empty:
        return customers_df
    df = customers_df.copy()
    if 'customer_id' in df.columns and 'customer_id' in purchases_df.columns:
        purchases_agg = purchases_df.groupby('customer_id').agg(
            order_count=('order_id', 'count'),
            total_spent=('order_value', 'sum')
        ).reset_index()
        df = df.merge(purchases_agg, on='customer_id', how='left')
        df['order_count'] = df['order_count'].fillna(0)
        df['total_spent'] = df['total_spent'].fillna(0)
        
        high_value_threshold = df['total_spent'].quantile(0.8) if len(df) > 0 else 0
        
        def segment(row):
            if row['order_count'] == 0: return 'No Purchase'
            elif row['order_count'] == 1: return 'One-time'
            elif row['total_spent'] >= high_value_threshold and high_value_threshold > 0: return 'High-value'
            else: return 'Repeat'
            
        df['customer_segment'] = df.apply(segment, axis=1)
    return df

def add_repeat_purchase_rate(purchases_df: pd.DataFrame) -> pd.DataFrame:
    """Per creator/campaign"""
    # this will return aggregated stats rather than append, or we can just return stats
    # Instructions: add_repeat_purchase_rate(purchases_df) — per creator/campaign
    # Actually just returns an aggregated dataframe or adds columns. Let's return a grouped DF.
    if purchases_df.empty:
        return pd.DataFrame()
    if 'campaign_id' in purchases_df.columns and 'customer_id' in purchases_df.columns:
        df = purchases_df.groupby(['campaign_id', 'customer_id']).size().reset_index(name='customer_orders')
        df['is_repeat'] = df['customer_orders'] > 1
        camp_agg = df.groupby('campaign_id').agg(
            total_customers=('customer_id', 'nunique'),
            repeat_customers=('is_repeat', 'sum')
        ).reset_index()
        camp_agg['repeat_purchase_rate'] = camp_agg.apply(
            lambda r: safe_divide(r['repeat_customers'], r['total_customers']) * 100, axis=1)
        return camp_agg
    return pd.DataFrame()

def add_revenue_per_customer(purchases_df: pd.DataFrame) -> float:
    """total revenue / unique customers"""
    if purchases_df.empty or 'order_value' not in purchases_df.columns or 'customer_id' not in purchases_df.columns:
        return 0.0
    return safe_divide(purchases_df['order_value'].sum(), purchases_df['customer_id'].nunique())

def add_aov(purchases_df: pd.DataFrame) -> float:
    """total revenue / total orders"""
    if purchases_df.empty or 'order_value' not in purchases_df.columns:
        return 0.0
    return safe_divide(purchases_df['order_value'].sum(), len(purchases_df))

def add_cac(campaigns_df: pd.DataFrame, customers_df: pd.DataFrame) -> float:
    """campaign_budget / new_customers"""
    if campaigns_df.empty or customers_df.empty or 'campaign_budget' not in campaigns_df.columns or 'referring_campaign_id' not in customers_df.columns:
        return 0.0
    total_budget = campaigns_df['campaign_budget'].sum()
    new_customers = customers_df['referring_campaign_id'].notna().sum()
    return safe_divide(total_budget, new_customers)

def build_analytics_dataset(data_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Merged analytical DataFrame"""
    if 'purchases' not in data_dict or 'campaigns' not in data_dict or 'creators' not in data_dict:
        return pd.DataFrame()
        
    purchases = data_dict['purchases']
    campaigns = data_dict['campaigns']
    creators = data_dict['creators']
    
    # Merge purchases with campaigns
    df = purchases.merge(campaigns, on='campaign_id', how='left')
    # Merge with creators
    df = df.merge(creators, on='creator_id', how='left')
    
    return df
