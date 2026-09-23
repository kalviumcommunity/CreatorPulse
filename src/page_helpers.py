"""Shared helpers for Streamlit pages — filtering, formatting, etc."""
import streamlit as st
import pandas as pd
from datetime import timedelta


def get_filtered_data():
    """Apply global sidebar filters from st.session_state to data.
    
    Reads:
      st.session_state.data_dict — dict of DataFrames
      st.session_state.filters — dict of selected filter values
    
    Returns:
      dict of filtered DataFrames (copies, not in-place)
    """
    data = st.session_state.get('data_dict', {})
    filters = st.session_state.get('filters', {})
    if not data:
        return {}

    result = {k: v.copy() for k, v in data.items()}

    # ---- Date filter on purchases ----
    dr = filters.get('date_range', 'All Time')
    if dr != 'All Time' and 'purchases' in result and 'purchase_date' in result['purchases'].columns:
        now = pd.Timestamp.now()
        if dr == 'Last 30 Days':
            start = now - timedelta(days=30)
        elif dr == 'Last 90 Days':
            start = now - timedelta(days=90)
        else:
            start = result['purchases']['purchase_date'].min()
        result['purchases'] = result['purchases'][result['purchases']['purchase_date'] >= start]

    # ---- Creator filter ----
    selected_creators = filters.get('creators', [])
    if selected_creators and 'creators' in result and 'creator_name' in result['creators'].columns:
        cids = result['creators'][result['creators']['creator_name'].isin(selected_creators)]['creator_id'].tolist()
        result['creators'] = result['creators'][result['creators']['creator_id'].isin(cids)]
        if 'campaigns' in result and 'creator_id' in result['campaigns'].columns:
            result['campaigns'] = result['campaigns'][result['campaigns']['creator_id'].isin(cids)]
        if 'purchases' in result and 'creator_id' in result['purchases'].columns:
            result['purchases'] = result['purchases'][result['purchases']['creator_id'].isin(cids)]

    # ---- Campaign filter ----
    selected_campaigns = filters.get('campaigns', [])
    if selected_campaigns and 'campaigns' in result and 'campaign_name' in result['campaigns'].columns:
        camp_ids = result['campaigns'][result['campaigns']['campaign_name'].isin(selected_campaigns)]['campaign_id'].tolist()
        result['campaigns'] = result['campaigns'][result['campaigns']['campaign_id'].isin(camp_ids)]
        if 'purchases' in result and 'campaign_id' in result['purchases'].columns:
            result['purchases'] = result['purchases'][result['purchases']['campaign_id'].isin(camp_ids)]

    # ---- Platform filter ----
    selected_platforms = filters.get('platforms', [])
    if selected_platforms and 'campaigns' in result and 'platform' in result['campaigns'].columns:
        result['campaigns'] = result['campaigns'][result['campaigns']['platform'].isin(selected_platforms)]

    # ---- Content type filter ----
    selected_ct = filters.get('content_types', [])
    if selected_ct and 'campaigns' in result and 'content_type' in result['campaigns'].columns:
        result['campaigns'] = result['campaigns'][result['campaigns']['content_type'].isin(selected_ct)]

    # ---- Tier filter ----
    selected_tiers = filters.get('tiers', [])
    if selected_tiers and 'creators' in result and 'creator_tier' in result['creators'].columns:
        result['creators'] = result['creators'][result['creators']['creator_tier'].isin(selected_tiers)]
        cids = result['creators']['creator_id'].tolist()
        if 'campaigns' in result and 'creator_id' in result['campaigns'].columns:
            result['campaigns'] = result['campaigns'][result['campaigns']['creator_id'].isin(cids)]
        if 'purchases' in result and 'creator_id' in result['purchases'].columns:
            result['purchases'] = result['purchases'][result['purchases']['creator_id'].isin(cids)]

    return result
