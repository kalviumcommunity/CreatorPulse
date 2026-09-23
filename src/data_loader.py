import pandas as pd
import streamlit as st
import os
from typing import Dict

@st.cache_data
def load_creators(path: str) -> pd.DataFrame:
    """Load creators dataset"""
    try:
        df = pd.read_csv(path, dtype={'creator_id': str})
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame()

@st.cache_data
def load_campaigns(path: str) -> pd.DataFrame:
    """Load campaigns dataset"""
    try:
        df = pd.read_csv(path, dtype={'campaign_id': str, 'creator_id': str})
        if 'campaign_start_date' in df.columns:
            df['campaign_start_date'] = pd.to_datetime(df['campaign_start_date'], errors='coerce')
        if 'campaign_end_date' in df.columns:
            df['campaign_end_date'] = pd.to_datetime(df['campaign_end_date'], errors='coerce')
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame()

@st.cache_data
def load_customers(path: str) -> pd.DataFrame:
    """Load customers dataset"""
    try:
        df = pd.read_csv(path, dtype={'customer_id': str, 'referring_creator_id': str, 'referring_campaign_id': str})
        if 'first_purchase_date' in df.columns:
            df['first_purchase_date'] = pd.to_datetime(df['first_purchase_date'], errors='coerce')
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame()

@st.cache_data
def load_purchases(path: str) -> pd.DataFrame:
    """Load purchases dataset"""
    try:
        df = pd.read_csv(path, dtype={'order_id': str, 'customer_id': str, 'creator_id': str, 'campaign_id': str, 'product_id': str})
        if 'purchase_date' in df.columns:
            df['purchase_date'] = pd.to_datetime(df['purchase_date'], errors='coerce')
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame()

@st.cache_data
def load_all_data(data_dir: str) -> Dict[str, pd.DataFrame]:
    """Load all datasets into a dictionary"""
    return {
        'creators': load_creators(os.path.join(data_dir, 'creators.csv')),
        'campaigns': load_campaigns(os.path.join(data_dir, 'campaigns.csv')),
        'customers': load_customers(os.path.join(data_dir, 'customers.csv')),
        'purchases': load_purchases(os.path.join(data_dir, 'purchases.csv'))
    }
