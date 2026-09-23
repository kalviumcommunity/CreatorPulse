"""Analytics module — Creator, Campaign, Customer, Funnel, Time-series, Correlation analytics."""
import pandas as pd
from typing import Dict, Any, List
from .utils import safe_divide


def build_creator_metrics(data_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build per-creator metrics: engagement, CTR, conversion, revenue, repeat purchase rate.
    
    Methodology:
    - Engagement Rate = (likes+comments+shares+saves) / impressions × 100  [Derived]
    - CTR = referral_clicks / impressions × 100  [Derived]
    - Conversion Rate = purchases / referral_clicks × 100  [Derived]
    - Repeat Purchase Rate = customers_with_2+_orders / unique_customers × 100  [Derived]
    """
    creators = data_dict.get('creators', pd.DataFrame())
    campaigns = data_dict.get('campaigns', pd.DataFrame())
    purchases = data_dict.get('purchases', pd.DataFrame())

    if creators.empty:
        return pd.DataFrame()

    df = creators[['creator_id', 'creator_name', 'followers', 'creator_category', 'creator_tier']].copy()

    # --- Campaign-level aggregation ---
    if not campaigns.empty and 'creator_id' in campaigns.columns:
        eng_cols = [c for c in ['likes', 'comments', 'shares', 'saves'] if c in campaigns.columns]
        camp_agg = campaigns.groupby('creator_id').agg(
            total_impressions=('impressions', 'sum'),
            total_referral_clicks=('referral_clicks', 'sum'),
            total_landing_page_visits=('landing_page_visits', 'sum'),
            total_engagements=('engagements', 'sum'),
            campaign_count=('campaign_id', 'nunique'),
            total_budget=('campaign_budget', 'sum'),
        ).reset_index()

        # Also sum individual engagement columns
        if eng_cols:
            for col in eng_cols:
                camp_eng = campaigns.groupby('creator_id')[col].sum().reset_index()
                camp_eng.columns = ['creator_id', f'total_{col}']
                camp_agg = camp_agg.merge(camp_eng, on='creator_id', how='left')

        df = df.merge(camp_agg, on='creator_id', how='left')
    else:
        df['total_impressions'] = 0
        df['total_referral_clicks'] = 0
        df['total_engagements'] = 0
        df['campaign_count'] = 0
        df['total_budget'] = 0

    # --- Purchase-level aggregation (purchases have creator_id directly) ---
    if not purchases.empty and 'creator_id' in purchases.columns:
        pur_agg = purchases.groupby('creator_id').agg(
            revenue=('order_value', 'sum'),
            total_orders=('order_id', 'nunique'),
            unique_customers=('customer_id', 'nunique'),
        ).reset_index()

        # Repeat customers per creator
        cust_orders = purchases.groupby(['creator_id', 'customer_id']).size().reset_index(name='order_count')
        repeat_agg = cust_orders.groupby('creator_id').agg(
            repeat_customers=('order_count', lambda x: (x > 1).sum()),
            total_cust_for_repeat=('customer_id', 'nunique'),
        ).reset_index()

        pur_agg = pur_agg.merge(repeat_agg, on='creator_id', how='left')
        df = df.merge(pur_agg, on='creator_id', how='left')
    else:
        df['revenue'] = 0.0
        df['total_orders'] = 0
        df['unique_customers'] = 0
        df['repeat_customers'] = 0
        df['total_cust_for_repeat'] = 0

    # Fill NaN
    for col in df.select_dtypes(include=['number']).columns:
        df[col] = df[col].fillna(0)

    # --- Derived metrics ---
    df['engagement_rate'] = df.apply(
        lambda r: safe_divide(r.get('total_engagements', 0), r.get('total_impressions', 0)) * 100, axis=1
    )
    df['ctr'] = df.apply(
        lambda r: safe_divide(r.get('total_referral_clicks', 0), r.get('total_impressions', 0)) * 100, axis=1
    )
    df['conversion_rate'] = df.apply(
        lambda r: safe_divide(r.get('total_orders', 0), r.get('total_referral_clicks', 0)) * 100, axis=1
    )
    df['repeat_purchase_rate'] = df.apply(
        lambda r: safe_divide(r.get('repeat_customers', 0), r.get('unique_customers', 0)) * 100, axis=1
    )
    df['aov'] = df.apply(
        lambda r: safe_divide(r.get('revenue', 0), r.get('total_orders', 0)), axis=1
    )
    df['revenue_per_customer'] = df.apply(
        lambda r: safe_divide(r.get('revenue', 0), r.get('unique_customers', 0)), axis=1
    )
    df['cac'] = df.apply(
        lambda r: safe_divide(r.get('total_budget', 0), r.get('unique_customers', 0)), axis=1
    )

    # Rename for display
    df = df.rename(columns={
        'total_impressions': 'impressions',
        'total_referral_clicks': 'referral_clicks',
        'total_engagements': 'engagements',
        'total_orders': 'purchases',
        'unique_customers': 'new_customers',
    })

    return df


def build_campaign_metrics(data_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build per-campaign metrics with engagement, conversion, revenue."""
    campaigns = data_dict.get('campaigns', pd.DataFrame())
    purchases = data_dict.get('purchases', pd.DataFrame())
    creators = data_dict.get('creators', pd.DataFrame())

    if campaigns.empty:
        return pd.DataFrame()

    df = campaigns.copy()

    # Add engagement rate and CTR
    eng_cols = [c for c in ['likes', 'comments', 'shares', 'saves'] if c in df.columns]
    if eng_cols and 'impressions' in df.columns:
        df['total_engagement'] = df[eng_cols].sum(axis=1)
        df['engagement_rate'] = df.apply(
            lambda r: safe_divide(r['total_engagement'], r['impressions']) * 100, axis=1
        )
    if 'referral_clicks' in df.columns and 'impressions' in df.columns:
        df['ctr'] = df.apply(
            lambda r: safe_divide(r['referral_clicks'], r['impressions']) * 100, axis=1
        )

    # Add purchase metrics per campaign
    if not purchases.empty and 'campaign_id' in purchases.columns:
        pur_agg = purchases.groupby('campaign_id').agg(
            total_purchases=('order_id', 'nunique'),
            revenue=('order_value', 'sum'),
            unique_customers=('customer_id', 'nunique'),
        ).reset_index()

        # Repeat customers per campaign
        cust_orders = purchases.groupby(['campaign_id', 'customer_id']).size().reset_index(name='order_count')
        repeat_agg = cust_orders.groupby('campaign_id').agg(
            repeat_customers=('order_count', lambda x: (x > 1).sum()),
        ).reset_index()
        pur_agg = pur_agg.merge(repeat_agg, on='campaign_id', how='left')

        df = df.merge(pur_agg, on='campaign_id', how='left')
        df['total_purchases'] = df['total_purchases'].fillna(0)
        df['revenue'] = df['revenue'].fillna(0)
        df['unique_customers'] = df['unique_customers'].fillna(0)
        df['repeat_customers'] = df['repeat_customers'].fillna(0)
    else:
        df['total_purchases'] = 0
        df['revenue'] = 0
        df['unique_customers'] = 0
        df['repeat_customers'] = 0

    # Conversion rate
    if 'referral_clicks' in df.columns:
        df['conversion_rate'] = df.apply(
            lambda r: safe_divide(r['total_purchases'], r['referral_clicks']) * 100, axis=1
        )
    df['repeat_purchase_rate'] = df.apply(
        lambda r: safe_divide(r['repeat_customers'], r['unique_customers']) * 100, axis=1
    )
    df['aov'] = df.apply(
        lambda r: safe_divide(r['revenue'], r['total_purchases']), axis=1
    )

    # ROI
    if 'campaign_budget' in df.columns:
        df['roi'] = df.apply(
            lambda r: safe_divide(r['revenue'] - r['campaign_budget'], r['campaign_budget']) * 100, axis=1
        )
        df['cac'] = df.apply(
            lambda r: safe_divide(r['campaign_budget'], r['unique_customers']), axis=1
        )

    # Add creator name
    if not creators.empty and 'creator_id' in df.columns and 'creator_id' in creators.columns:
        df = df.merge(creators[['creator_id', 'creator_name']], on='creator_id', how='left')

    return df


def build_customer_metrics(data_dict: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """Customer segmentation, distributions, and summary metrics."""
    customers = data_dict.get('customers', pd.DataFrame())
    purchases = data_dict.get('purchases', pd.DataFrame())

    if purchases.empty or 'customer_id' not in purchases.columns:
        return {}

    # Purchase frequency per customer
    cust_stats = purchases.groupby('customer_id').agg(
        order_count=('order_id', 'nunique'),
        total_spent=('order_value', 'sum'),
        first_purchase=('purchase_date', 'min'),
        last_purchase=('purchase_date', 'max'),
    ).reset_index()

    unique_customers = len(cust_stats)
    one_time = int((cust_stats['order_count'] == 1).sum())
    repeat = int((cust_stats['order_count'] > 1).sum())

    # High-value: top 20% by total_spent
    threshold = cust_stats['total_spent'].quantile(0.80) if len(cust_stats) > 0 else 0
    high_value = int((cust_stats['total_spent'] >= threshold).sum())

    # Segment labels
    def segment(row):
        if row['total_spent'] >= threshold:
            return 'High-value'
        elif row['order_count'] > 1:
            return 'Repeat'
        else:
            return 'One-time'

    cust_stats['customer_segment'] = cust_stats.apply(segment, axis=1)

    # Frequency distribution
    freq_dist = {}
    for i in range(1, 4):
        freq_dist[f'{i} purchase{"s" if i > 1 else ""}'] = int((cust_stats['order_count'] == i).sum())
    freq_dist['4+ purchases'] = int((cust_stats['order_count'] >= 4).sum())

    avg_orders = cust_stats['order_count'].mean() if len(cust_stats) > 0 else 0
    avg_revenue = cust_stats['total_spent'].mean() if len(cust_stats) > 0 else 0

    return {
        'unique_customers': unique_customers,
        'one_time': one_time,
        'repeat': repeat,
        'high_value': high_value,
        'high_value_threshold': float(threshold),
        'avg_orders_per_customer': float(avg_orders),
        'avg_revenue_per_customer': float(avg_revenue),
        'segment_counts': cust_stats['customer_segment'].value_counts().to_dict(),
        'frequency_distribution': freq_dist,
        'customer_data': cust_stats,
    }


def build_funnel_metrics(data_dict: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
    """Full acquisition funnel: Impressions → Engagements → Referral Clicks → 
    Landing Page Visits → Purchases → Repeat Purchases.
    
    Only displays stages that exist in the data.
    """
    campaigns = data_dict.get('campaigns', pd.DataFrame())
    purchases = data_dict.get('purchases', pd.DataFrame())

    if campaigns.empty:
        return []

    stages = []

    # Stage 1: Impressions
    if 'impressions' in campaigns.columns:
        stages.append({"stage": "Impressions", "volume": int(campaigns['impressions'].sum())})

    # Stage 2: Engagements
    if 'engagements' in campaigns.columns:
        stages.append({"stage": "Engagements", "volume": int(campaigns['engagements'].sum())})

    # Stage 3: Referral Clicks
    if 'referral_clicks' in campaigns.columns:
        stages.append({"stage": "Referral Clicks", "volume": int(campaigns['referral_clicks'].dropna().sum())})

    # Stage 4: Landing Page Visits
    if 'landing_page_visits' in campaigns.columns:
        stages.append({"stage": "Landing Page Visits", "volume": int(campaigns['landing_page_visits'].sum())})

    # Stage 5: Purchases
    if not purchases.empty:
        stages.append({"stage": "Purchases", "volume": int(purchases['order_id'].nunique())})

        # Stage 6: Repeat Purchases (customers with 2+ orders)
        if 'customer_id' in purchases.columns:
            cust_counts = purchases.groupby('customer_id').size()
            repeat_customers = int((cust_counts > 1).sum())
            stages.append({"stage": "Repeat Customers", "volume": repeat_customers})

    # Calculate conversion and drop-off percentages
    for i, s in enumerate(stages):
        if i == 0:
            s['pct_of_previous'] = 100.0
            s['dropoff_pct'] = 0.0
        else:
            prev = stages[i - 1]['volume']
            s['pct_of_previous'] = round(safe_divide(s['volume'], prev) * 100.0, 2)
            s['dropoff_pct'] = round(100.0 - s['pct_of_previous'], 2)

    return stages


def build_time_series(data_dict: Dict[str, pd.DataFrame], freq: str = 'M') -> pd.DataFrame:
    """Monthly time-series metrics from purchases."""
    purchases = data_dict.get('purchases', pd.DataFrame())
    if purchases.empty or 'purchase_date' not in purchases.columns:
        return pd.DataFrame()

    df = purchases.copy()
    if not pd.api.types.is_datetime64_any_dtype(df['purchase_date']):
        df['purchase_date'] = pd.to_datetime(df['purchase_date'], errors='coerce')
    df = df.dropna(subset=['purchase_date'])

    # Monthly aggregation
    df['month'] = df['purchase_date'].dt.to_period(freq)
    monthly = df.groupby('month').agg(
        revenue=('order_value', 'sum'),
        orders=('order_id', 'nunique'),
        unique_customers=('customer_id', 'nunique'),
    ).reset_index()
    monthly['month'] = monthly['month'].dt.to_timestamp()

    return monthly


def build_correlation_matrix(analytics_df: pd.DataFrame) -> pd.DataFrame:
    """Correlation matrix for numeric variables. Note: correlation ≠ causation."""
    if analytics_df.empty:
        return pd.DataFrame()
    numeric_cols = analytics_df.select_dtypes(include=['number'])
    if numeric_cols.empty:
        return pd.DataFrame()
    return numeric_cols.corr()


def build_creator_patterns(creator_metrics_df: pd.DataFrame) -> pd.DataFrame:
    """Label creators by engagement-conversion pattern.
    
    Patterns (using median as threshold):
    - High Eng / Low Conv: Above-median engagement, below-median conversion
    - Low Eng / High Conv: Below-median engagement, above-median conversion
    - High Eng / High Conv: Both above median
    - Low Eng / Low Conv: Both below median
    """
    if creator_metrics_df.empty:
        return creator_metrics_df
    df = creator_metrics_df.copy()

    if 'engagement_rate' not in df.columns or 'conversion_rate' not in df.columns:
        return df

    eng_median = df['engagement_rate'].median()
    conv_median = df['conversion_rate'].median()
    rep_median = df['repeat_purchase_rate'].median() if 'repeat_purchase_rate' in df.columns else 0

    def label_pattern(row):
        high_eng = row['engagement_rate'] > eng_median
        high_conv = row['conversion_rate'] > conv_median
        high_rep = row.get('repeat_purchase_rate', 0) > rep_median if rep_median > 0 else False

        if high_eng and not high_conv:
            return 'High Eng / Low Conv'
        elif not high_eng and high_conv:
            return 'Low Eng / High Conv'
        elif high_eng and high_conv:
            return 'High Eng / High Conv'
        else:
            return 'Low Eng / Low Conv'

    df['pattern_label'] = df.apply(label_pattern, axis=1)
    df['eng_median'] = eng_median
    df['conv_median'] = conv_median

    return df


def build_content_type_metrics(data_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Metrics grouped by content_type — engagement, CTR, conversion, revenue."""
    campaigns = data_dict.get('campaigns', pd.DataFrame())
    purchases = data_dict.get('purchases', pd.DataFrame())

    if campaigns.empty or 'content_type' not in campaigns.columns:
        return pd.DataFrame()

    # Campaign-level agg by content type
    eng_cols = [c for c in ['likes', 'comments', 'shares', 'saves'] if c in campaigns.columns]
    agg_dict = {
        'campaign_id': 'nunique',
        'impressions': 'sum',
        'referral_clicks': 'sum',
        'engagements': 'sum',
    }
    if 'campaign_budget' in campaigns.columns:
        agg_dict['campaign_budget'] = 'sum'

    ct = campaigns.groupby('content_type').agg(**{k: (k, v) for k, v in agg_dict.items()}).reset_index()
    ct = ct.rename(columns={'campaign_id': 'campaigns'})

    # Purchase-level agg by content type (via campaign_id)
    if not purchases.empty and 'campaign_id' in purchases.columns:
        camp_ct = campaigns[['campaign_id', 'content_type']].drop_duplicates()
        pur_ct = purchases.merge(camp_ct, on='campaign_id', how='left')
        pur_agg = pur_ct.groupby('content_type').agg(
            total_purchases=('order_id', 'nunique'),
            revenue=('order_value', 'sum'),
            unique_customers=('customer_id', 'nunique'),
        ).reset_index()

        # Repeat per content type
        cust_ct = pur_ct.groupby(['content_type', 'customer_id']).size().reset_index(name='oc')
        rep_ct = cust_ct.groupby('content_type').agg(
            repeat_customers=('oc', lambda x: (x > 1).sum()),
        ).reset_index()
        pur_agg = pur_agg.merge(rep_ct, on='content_type', how='left').fillna(0)

        ct = ct.merge(pur_agg, on='content_type', how='left').fillna(0)
    else:
        ct['total_purchases'] = 0
        ct['revenue'] = 0
        ct['unique_customers'] = 0
        ct['repeat_customers'] = 0

    # Derived
    ct['engagement_rate'] = ct.apply(lambda r: safe_divide(r['engagements'], r['impressions']) * 100, axis=1)
    ct['ctr'] = ct.apply(lambda r: safe_divide(r['referral_clicks'], r['impressions']) * 100, axis=1)
    ct['conversion_rate'] = ct.apply(lambda r: safe_divide(r['total_purchases'], r['referral_clicks']) * 100, axis=1)
    ct['repeat_purchase_rate'] = ct.apply(lambda r: safe_divide(r['repeat_customers'], r['unique_customers']) * 100, axis=1)

    return ct


def build_cohort_analysis(data_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Monthly cohort retention analysis."""
    purchases = data_dict.get('purchases', pd.DataFrame())
    if purchases.empty or 'customer_id' not in purchases.columns or 'purchase_date' not in purchases.columns:
        return pd.DataFrame()

    df = purchases.copy()
    if not pd.api.types.is_datetime64_any_dtype(df['purchase_date']):
        df['purchase_date'] = pd.to_datetime(df['purchase_date'], errors='coerce')
    df = df.dropna(subset=['purchase_date'])

    df['order_month'] = df['purchase_date'].dt.to_period('M')
    cohorts = df.groupby('customer_id')['order_month'].min().reset_index()
    cohorts.columns = ['customer_id', 'cohort_month']

    df = df.merge(cohorts, on='customer_id')
    df['cohort_index'] = (df['order_month'] - df['cohort_month']).apply(lambda x: x.n)

    cohort_counts = df.groupby(['cohort_month', 'cohort_index'])['customer_id'].nunique().reset_index()
    pivot = cohort_counts.pivot(index='cohort_month', columns='cohort_index', values='customer_id')

    return pivot
