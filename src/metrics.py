"""Metrics module — KPI calculation functions for CreatorPulse."""
import pandas as pd
from typing import Dict, Any
from .utils import safe_divide


def calculate_total_revenue(purchases_df: pd.DataFrame) -> float:
    """Total revenue from purchases. Classification: Observed."""
    if purchases_df.empty or 'order_value' not in purchases_df.columns:
        return 0.0
    return float(purchases_df['order_value'].sum())


def calculate_total_orders(purchases_df: pd.DataFrame) -> int:
    """Total number of unique orders. Classification: Observed."""
    if purchases_df.empty:
        return 0
    if 'order_id' in purchases_df.columns:
        return int(purchases_df['order_id'].nunique())
    return len(purchases_df)


def calculate_unique_customers(purchases_df: pd.DataFrame) -> int:
    """Number of unique customers who made a purchase. Classification: Observed."""
    if purchases_df.empty or 'customer_id' not in purchases_df.columns:
        return 0
    return int(purchases_df['customer_id'].nunique())


def calculate_new_customers(customers_df: pd.DataFrame, purchases_df: pd.DataFrame) -> int:
    """Number of new customers acquired (unique customers in the customers table).
    Classification: Observed."""
    if not customers_df.empty and 'customer_id' in customers_df.columns:
        return int(customers_df['customer_id'].nunique())
    if not purchases_df.empty and 'customer_id' in purchases_df.columns:
        return int(purchases_df['customer_id'].nunique())
    return 0


def calculate_repeat_customers(purchases_df: pd.DataFrame) -> int:
    """Number of customers with 2+ purchases. Classification: Derived."""
    if purchases_df.empty or 'customer_id' not in purchases_df.columns:
        return 0
    counts = purchases_df.groupby('customer_id').size()
    return int((counts > 1).sum())


def calculate_repeat_purchase_rate(purchases_df: pd.DataFrame) -> float:
    """Repeat customers / Total unique customers × 100. Classification: Derived."""
    unique = calculate_unique_customers(purchases_df)
    repeat = calculate_repeat_customers(purchases_df)
    return safe_divide(repeat, unique) * 100.0


def calculate_aov(purchases_df: pd.DataFrame) -> float:
    """Average Order Value = total_revenue / total_orders. Classification: Derived."""
    return safe_divide(
        calculate_total_revenue(purchases_df),
        calculate_total_orders(purchases_df)
    )


def calculate_engagement_rate(campaigns_df: pd.DataFrame) -> float:
    """Overall engagement rate = sum(likes+comments+shares+saves) / sum(impressions) × 100.
    Classification: Derived."""
    if campaigns_df.empty or 'impressions' not in campaigns_df.columns:
        return 0.0
    eng_cols = ['likes', 'comments', 'shares', 'saves']
    available_cols = [c for c in eng_cols if c in campaigns_df.columns]
    if not available_cols:
        if 'engagements' in campaigns_df.columns:
            total_eng = campaigns_df['engagements'].sum()
        else:
            return 0.0
    else:
        total_eng = campaigns_df[available_cols].sum().sum()
    total_imp = campaigns_df['impressions'].sum()
    return safe_divide(total_eng, total_imp) * 100.0


def calculate_overall_ctr(campaigns_df: pd.DataFrame) -> float:
    """Overall CTR = total referral clicks / total impressions × 100.
    Classification: Derived."""
    if campaigns_df.empty or 'referral_clicks' not in campaigns_df.columns or 'impressions' not in campaigns_df.columns:
        return 0.0
    return safe_divide(
        campaigns_df['referral_clicks'].sum(),
        campaigns_df['impressions'].sum()
    ) * 100.0


def calculate_overall_conversion_rate(campaigns_df: pd.DataFrame, purchases_df: pd.DataFrame) -> float:
    """Overall conversion rate = total unique purchases / total referral clicks × 100.
    Denominator: referral_clicks. Classification: Derived."""
    if campaigns_df.empty or purchases_df.empty or 'referral_clicks' not in campaigns_df.columns:
        return 0.0
    total_purchases = purchases_df['order_id'].nunique() if 'order_id' in purchases_df.columns else len(purchases_df)
    total_clicks = campaigns_df['referral_clicks'].sum()
    return safe_divide(total_purchases, total_clicks) * 100.0


def calculate_cac(campaigns_df: pd.DataFrame, customers_df: pd.DataFrame) -> float:
    """Customer Acquisition Cost = total campaign_budget / new customers.
    Classification: Derived. Returns 0.0 if budget data unavailable."""
    if campaigns_df.empty or 'campaign_budget' not in campaigns_df.columns:
        return 0.0
    total_budget = campaigns_df['campaign_budget'].sum()
    new_custs = calculate_new_customers(customers_df, pd.DataFrame())
    if new_custs == 0:
        return 0.0
    return safe_divide(total_budget, new_custs)


def calculate_overview_kpis(data_dict: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """Calculate all overview KPIs. Returns dict of named metrics."""
    purchases = data_dict.get('purchases', pd.DataFrame())
    campaigns = data_dict.get('campaigns', pd.DataFrame())
    customers = data_dict.get('customers', pd.DataFrame())

    return {
        'total_revenue': calculate_total_revenue(purchases),
        'total_orders': calculate_total_orders(purchases),
        'unique_customers': calculate_unique_customers(purchases),
        'new_customers': calculate_new_customers(customers, purchases),
        'repeat_customers': calculate_repeat_customers(purchases),
        'repeat_purchase_rate': calculate_repeat_purchase_rate(purchases),
        'aov': calculate_aov(purchases),
        'engagement_rate': calculate_engagement_rate(campaigns),
        'overall_ctr': calculate_overall_ctr(campaigns),
        'overall_conversion_rate': calculate_overall_conversion_rate(campaigns, purchases),
        'cac': calculate_cac(campaigns, customers),
    }
