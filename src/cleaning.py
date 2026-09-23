"""Cleaning module — Data cleaning, deduplication, and missing value handling."""
import pandas as pd
from typing import Dict, Any, Tuple


def clean_creators(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize creator_name, standardize creator_category, validate follower counts."""
    if df.empty:
        return df
    df = df.copy()
    if 'creator_name' in df.columns:
        df['creator_name'] = df['creator_name'].str.strip().str.title()
    if 'creator_category' in df.columns:
        df['creator_category'] = df['creator_category'].str.strip().str.title()
    if 'followers' in df.columns:
        df['followers'] = pd.to_numeric(df['followers'], errors='coerce').fillna(0).astype(int)
        df.loc[df['followers'] < 0, 'followers'] = 0
    if 'creator_id' in df.columns:
        df['creator_id'] = df['creator_id'].astype(str).str.strip()
    return df


def clean_campaigns(df: pd.DataFrame) -> pd.DataFrame:
    """Parse dates, clean budget, normalize content_type/platform, handle negative saves."""
    if df.empty:
        return df
    df = df.copy()
    for date_col in ['campaign_start_date', 'campaign_end_date']:
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    if 'campaign_budget' in df.columns:
        df['campaign_budget'] = (
            df['campaign_budget'].astype(str)
            .str.replace('₹', '', regex=False)
            .str.replace(',', '', regex=False)
            .str.strip()
        )
        df['campaign_budget'] = pd.to_numeric(df['campaign_budget'], errors='coerce').fillna(0.0)
    if 'content_type' in df.columns:
        df['content_type'] = df['content_type'].str.strip().str.title()
    if 'platform' in df.columns:
        df['platform'] = df['platform'].str.strip().str.title()
    # Handle negative saves (clamp to 0, flag)
    if 'saves' in df.columns:
        df['has_negative_saves'] = df['saves'] < 0
        df.loc[df['saves'] < 0, 'saves'] = 0
    # Recalculate engagements if individual columns exist
    eng_cols = ['likes', 'comments', 'shares', 'saves']
    if all(c in df.columns for c in eng_cols):
        df['engagements'] = df[eng_cols].sum(axis=1)
    if 'creator_id' in df.columns:
        df['creator_id'] = df['creator_id'].astype(str).str.strip()
    if 'campaign_id' in df.columns:
        df['campaign_id'] = df['campaign_id'].astype(str).str.strip()
    return df


def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    """Parse dates, validate IDs."""
    if df.empty:
        return df
    df = df.copy()
    if 'first_purchase_date' in df.columns:
        df['first_purchase_date'] = pd.to_datetime(df['first_purchase_date'], errors='coerce')
    if 'customer_id' in df.columns:
        df['customer_id'] = df['customer_id'].astype(str).str.strip()
        df = df.dropna(subset=['customer_id'])
    if 'referring_creator_id' in df.columns:
        df['referring_creator_id'] = df['referring_creator_id'].astype(str).str.strip()
    if 'referring_campaign_id' in df.columns:
        df['referring_campaign_id'] = df['referring_campaign_id'].astype(str).str.strip()
    return df


def clean_purchases(df: pd.DataFrame) -> pd.DataFrame:
    """Parse dates, flag negative order_value as refunds, validate order_id."""
    if df.empty:
        return df
    df = df.copy()
    if 'purchase_date' in df.columns:
        df['purchase_date'] = pd.to_datetime(df['purchase_date'], errors='coerce')
    if 'order_id' in df.columns:
        df['order_id'] = df['order_id'].astype(str).str.strip()
        df = df.dropna(subset=['order_id'])
    if 'order_value' in df.columns:
        df['order_value'] = pd.to_numeric(df['order_value'], errors='coerce').fillna(0.0)
        df['is_refund'] = df['order_value'] < 0
    if 'customer_id' in df.columns:
        df['customer_id'] = df['customer_id'].astype(str).str.strip()
    if 'creator_id' in df.columns:
        df['creator_id'] = df['creator_id'].astype(str).str.strip()
    if 'campaign_id' in df.columns:
        df['campaign_id'] = df['campaign_id'].astype(str).str.strip()
    return df


def detect_duplicates(df: pd.DataFrame, subset: list = None) -> Dict[str, Any]:
    """Returns duplicate info dict."""
    if df.empty:
        return {"total_rows": 0, "duplicate_rows": 0, "duplicate_percentage": 0.0}
    dups = df.duplicated(subset=subset).sum()
    return {
        "total_rows": len(df),
        "duplicate_rows": int(dups),
        "duplicate_percentage": float(dups / len(df) * 100) if len(df) > 0 else 0.0,
    }


def remove_duplicates(df: pd.DataFrame, subset: list = None, keep: str = 'first') -> pd.DataFrame:
    """Deduplicate with logging."""
    if df.empty:
        return df
    before = len(df)
    df = df.drop_duplicates(subset=subset, keep=keep)
    removed = before - len(df)
    if removed > 0:
        pass  # Could log: f"Removed {removed} duplicate rows"
    return df


def handle_missing_values(df: pd.DataFrame, strategy_map: Dict[str, Any]) -> pd.DataFrame:
    """Per-column missing value strategy: 'drop', 'mean', 'median', 'mode', or a fill value."""
    if df.empty:
        return df
    df = df.copy()
    for col, strategy in strategy_map.items():
        if col in df.columns:
            if strategy == 'drop':
                df = df.dropna(subset=[col])
            elif strategy == 'mean':
                df[col] = df[col].fillna(df[col].mean())
            elif strategy == 'median':
                df[col] = df[col].fillna(df[col].median())
            elif strategy == 'mode':
                mode_val = df[col].mode()
                df[col] = df[col].fillna(mode_val.iloc[0] if not mode_val.empty else 0)
            else:
                df[col] = df[col].fillna(strategy)
    return df


def clean_all_data(data_dict: Dict[str, pd.DataFrame]) -> Tuple[Dict[str, pd.DataFrame], Dict[str, Any]]:
    """Clean all datasets and generate a cleaning report.
    
    Deduplication strategy:
    - creators: full row dedup
    - campaigns: dedup by campaign_id
    - customers: dedup by customer_id
    - purchases: dedup by order_id (keep first occurrence)
    """
    cleaned_dict = {}
    report = {}

    if 'creators' in data_dict:
        cleaned_dict['creators'] = clean_creators(data_dict['creators'])
        report['creators_dups'] = detect_duplicates(cleaned_dict['creators'])
        cleaned_dict['creators'] = remove_duplicates(cleaned_dict['creators'])

    if 'campaigns' in data_dict:
        cleaned_dict['campaigns'] = clean_campaigns(data_dict['campaigns'])
        report['campaigns_dups'] = detect_duplicates(cleaned_dict['campaigns'], subset=['campaign_id'])
        cleaned_dict['campaigns'] = remove_duplicates(cleaned_dict['campaigns'], subset=['campaign_id'])

    if 'customers' in data_dict:
        cleaned_dict['customers'] = clean_customers(data_dict['customers'])
        report['customers_dups'] = detect_duplicates(cleaned_dict['customers'], subset=['customer_id'])
        cleaned_dict['customers'] = remove_duplicates(cleaned_dict['customers'], subset=['customer_id'])

    if 'purchases' in data_dict:
        cleaned_dict['purchases'] = clean_purchases(data_dict['purchases'])
        report['purchases_dups_full'] = detect_duplicates(cleaned_dict['purchases'])
        report['purchases_dups_orderid'] = detect_duplicates(cleaned_dict['purchases'], subset=['order_id'])
        cleaned_dict['purchases'] = remove_duplicates(cleaned_dict['purchases'], subset=['order_id'])

    return cleaned_dict, report
