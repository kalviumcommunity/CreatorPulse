"""Validation module — Schema, referential integrity, business rules, profiling."""
import pandas as pd
from typing import Dict, Any, List


def validate_schema(df: pd.DataFrame, expected_columns: List[str]) -> bool:
    """Check that all expected columns exist in dataframe."""
    if df.empty and not expected_columns:
        return True
    return all(col in df.columns for col in expected_columns)


def validate_referential_integrity(data_dict: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
    """Check foreign key relationships between tables."""
    results = []

    # campaigns.creator_id → creators.creator_id
    if 'campaigns' in data_dict and 'creators' in data_dict:
        camp = data_dict['campaigns']
        cr = data_dict['creators']
        if 'creator_id' in camp.columns and 'creator_id' in cr.columns:
            invalid = camp[~camp['creator_id'].isin(cr['creator_id'])]
            results.append({
                "check": "campaigns→creators FK",
                "status": len(invalid) == 0,
                "details": f"{len(invalid)} invalid creator_ids in campaigns"
            })

    # purchases.customer_id → customers.customer_id
    if 'purchases' in data_dict and 'customers' in data_dict:
        pur = data_dict['purchases']
        cust = data_dict['customers']
        if 'customer_id' in pur.columns and 'customer_id' in cust.columns:
            invalid = pur[~pur['customer_id'].isin(cust['customer_id'])]
            results.append({
                "check": "purchases→customers FK",
                "status": len(invalid) == 0,
                "details": f"{len(invalid)} invalid customer_ids in purchases"
            })

    # purchases.campaign_id → campaigns.campaign_id
    if 'purchases' in data_dict and 'campaigns' in data_dict:
        pur = data_dict['purchases']
        camp = data_dict['campaigns']
        if 'campaign_id' in pur.columns and 'campaign_id' in camp.columns:
            invalid = pur[~pur['campaign_id'].isin(camp['campaign_id'])]
            results.append({
                "check": "purchases→campaigns FK",
                "status": len(invalid) == 0,
                "details": f"{len(invalid)} invalid campaign_ids in purchases"
            })

    return results


def validate_business_rules(data_dict: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
    """Check business rule constraints."""
    results = []
    if 'campaigns' in data_dict:
        df = data_dict['campaigns']
        # Clicks should not exceed impressions
        if 'impressions' in df.columns and 'referral_clicks' in df.columns:
            invalid = df[df['referral_clicks'] > df['impressions']]
            results.append({
                "check": "Clicks ≤ Impressions",
                "status": len(invalid) == 0,
                "details": f"{len(invalid)} rows where clicks > impressions"
            })
        # Non-negative engagement metrics
        for col in ['likes', 'comments', 'shares', 'saves']:
            if col in df.columns:
                neg = df[df[col] < 0]
                results.append({
                    "check": f"{col} ≥ 0",
                    "status": len(neg) == 0,
                    "details": f"{len(neg)} negative {col} values"
                })
        # Budget should be positive
        if 'campaign_budget' in df.columns:
            neg_budget = df[df['campaign_budget'] < 0]
            results.append({
                "check": "Budget ≥ 0",
                "status": len(neg_budget) == 0,
                "details": f"{len(neg_budget)} negative budget values"
            })

    if 'purchases' in data_dict:
        df = data_dict['purchases']
        if 'order_value' in df.columns:
            neg = df[df['order_value'] < 0]
            results.append({
                "check": "Negative order values (refunds)",
                "status": len(neg) == 0,
                "details": f"{len(neg)} negative order values (flagged as potential refunds)"
            })

    return results


def validate_date_ranges(df: pd.DataFrame, date_col: str) -> Dict[str, Any]:
    """Check for future dates and invalid dates."""
    if df.empty or date_col not in df.columns:
        return {"check": f"{date_col} valid", "status": True, "details": "No data"}

    dates = pd.to_datetime(df[date_col], errors='coerce')
    null_dates = dates.isna().sum()
    future = dates[dates > pd.Timestamp.now()]

    status = len(future) == 0 and null_dates == 0
    details_parts = []
    if len(future) > 0:
        details_parts.append(f"{len(future)} future dates")
    if null_dates > 0:
        details_parts.append(f"{null_dates} invalid/null dates")
    if not details_parts:
        details_parts.append("All dates valid")

    return {"check": f"{date_col} valid", "status": status, "details": "; ".join(details_parts)}


def validate_numeric_ranges(df: pd.DataFrame, col: str, min_val: float, max_val: float) -> Dict[str, Any]:
    """Check numeric column is within expected range."""
    if df.empty or col not in df.columns:
        return {"check": f"{col} range", "status": True, "details": "No data"}
    invalid = df[(df[col] < min_val) | (df[col] > max_val)]
    return {
        "check": f"{col} in [{min_val}, {max_val}]",
        "status": len(invalid) == 0,
        "details": f"{len(invalid)} out of range"
    }


def generate_validation_report(data_dict: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
    """Generate comprehensive validation report."""
    report = []
    report.extend(validate_referential_integrity(data_dict))
    report.extend(validate_business_rules(data_dict))

    if 'campaigns' in data_dict:
        report.append(validate_date_ranges(data_dict['campaigns'], 'campaign_start_date'))
        report.append(validate_date_ranges(data_dict['campaigns'], 'campaign_end_date'))
        report.append(validate_numeric_ranges(data_dict['campaigns'], 'campaign_budget', 0, float('inf')))

    if 'purchases' in data_dict:
        report.append(validate_date_ranges(data_dict['purchases'], 'purchase_date'))

    if 'customers' in data_dict:
        report.append(validate_date_ranges(data_dict['customers'], 'first_purchase_date'))

    return report


def profile_dataset(df: pd.DataFrame, name: str) -> Dict[str, Any]:
    """Profile a dataset: rows, columns, types, missing values, duplicates, numeric stats."""
    if df.empty:
        return {"name": name, "rows": 0, "columns": 0}

    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)

    # Date ranges
    date_ranges = {}
    for col in df.select_dtypes(include=['datetime64']).columns:
        date_ranges[col] = {
            "min": str(df[col].min()),
            "max": str(df[col].max()),
        }

    return {
        "name": name,
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "missing_values": missing[missing > 0].to_dict(),
        "missing_pct": missing_pct[missing_pct > 0].to_dict(),
        "total_missing_pct": round(df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100, 2),
        "duplicates": int(df.duplicated().sum()),
        "date_ranges": date_ranges,
    }
