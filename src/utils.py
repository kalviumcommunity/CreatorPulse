import pandas as pd
from typing import Dict, Any, Union

def safe_divide(numerator: Union[float, int], denominator: Union[float, int], default: float = 0.0) -> float:
    """Safely divide two numbers, returning a default value if the denominator is 0."""
    try:
        if pd.isna(denominator) or denominator == 0:
            return default
        return float(numerator) / float(denominator)
    except (TypeError, ValueError, ZeroDivisionError):
        return default

def format_currency(value: Union[float, int]) -> str:
    """Formats value as ₹X.XL or ₹X.XK"""
    if pd.isna(value):
        return "₹0.00"
    if value >= 10000000:
        return f"₹{value / 10000000:.2f}Cr"
    elif value >= 100000:
        return f"₹{value / 100000:.2f}L"
    elif value >= 1000:
        return f"₹{value / 1000:.2f}K"
    else:
        return f"₹{value:.2f}"

def format_percentage(value: Union[float, int]) -> str:
    """Formats value as X.X%"""
    if pd.isna(value):
        return "0.0%"
    return f"{value:.1f}%"

def format_number(value: Union[float, int]) -> str:
    """Formats large numbers with K/L/Cr suffixes"""
    if pd.isna(value):
        return "0"
    if value >= 10000000:
        return f"{value / 10000000:.2f}Cr"
    elif value >= 100000:
        return f"{value / 100000:.2f}L"
    elif value >= 1000:
        return f"{value / 1000:.2f}K"
    else:
        return f"{int(value)}" if float(value).is_integer() else f"{value:.2f}"

def apply_date_filter(df: pd.DataFrame, date_col: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Filters df by date range"""
    if df.empty or date_col not in df.columns:
        return df
    try:
        mask = (df[date_col] >= pd.to_datetime(start_date)) & (df[date_col] <= pd.to_datetime(end_date))
        return df.loc[mask]
    except Exception:
        return df

def apply_filters(df: pd.DataFrame, filters_dict: Dict[str, Any]) -> pd.DataFrame:
    """Applies multiple column filters"""
    if df.empty:
        return df
    filtered_df = df.copy()
    for col, value in filters_dict.items():
        if col in filtered_df.columns:
            if isinstance(value, list) and value:
                filtered_df = filtered_df[filtered_df[col].isin(value)]
            elif not isinstance(value, list):
                filtered_df = filtered_df[filtered_df[col] == value]
    return filtered_df
