import streamlit as st
import os
import sys
import pandas as pd
from datetime import datetime, timedelta

# Add parent directory to path so we can import src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from src.data_loader import load_all_data
    from src.cleaning import clean_all_data
    from src.utils import apply_filters
except ImportError:
    # Define stubs or print warning
    def load_all_data(data_dir): return {}
    def clean_all_data(data_dict): return {}, ""
    def apply_filters(df, **kwargs): return df

st.set_page_config(page_title='CreatorPulse', page_icon=':material/analytics:', layout='wide')

st.markdown('''
<style>
    .main .block-container { padding-top: 2rem; max-width: 1200px; }
    
    /* Sleeker Metric Cards */
    [data-testid="stMetric"] { 
        background: #ffffff; 
        border-radius: 10px; 
        padding: 1.2rem; 
        border: 1px solid #e0e6ed; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04);
        border-color: #cbd5e1;
    }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 700; color: #0f172a !important; }
    div[data-testid="stMetricLabel"], div[data-testid="stMetricLabel"] p { font-size: 0.95rem; font-weight: 500; color: #64748b !important; }
    
    /* Insight Cards */
    .insight-card { 
        background: #ffffff; 
        border-left: 4px solid #3b82f6; 
        border-radius: 8px; 
        padding: 1.25rem 1.5rem; 
        margin-bottom: 1.25rem; 
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); 
        border-top: 1px solid #f1f5f9;
        border-right: 1px solid #f1f5f9;
        border-bottom: 1px solid #f1f5f9;
    }
    
    /* Sidebar styling tweaks */
    [data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }
</style>
''', unsafe_allow_html=True)

@st.cache_data
def load_and_prep_data():
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'demo')
    try:
        raw_data = load_all_data(data_dir)
        cleaned_data, _ = clean_all_data(raw_data)
        return cleaned_data
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return {}

def init_session_state():
    if 'data_dict' not in st.session_state:
        st.session_state.data_dict = load_and_prep_data()

init_session_state()

# Sidebar
st.sidebar.info('Demo Mode — Insights are generated from synthetic development data.', icon=":material/warning:")

# Global filters
st.sidebar.header("Global Filters")
date_range = st.sidebar.selectbox("Date Range", ["All Time", "Last 30 Days", "Last 90 Days", "Custom"])

if 'campaigns' in st.session_state.data_dict and not st.session_state.data_dict['campaigns'].empty:
    campaigns_df = st.session_state.data_dict['campaigns']
    creators_df = st.session_state.data_dict.get('creators', pd.DataFrame())
    
    creators = sorted(creators_df['creator_name'].dropna().unique()) if 'creator_name' in creators_df else []
    campaign_names = sorted(campaigns_df['campaign_name'].dropna().unique()) if 'campaign_name' in campaigns_df else []
    platforms = sorted(campaigns_df['platform'].dropna().unique()) if 'platform' in campaigns_df else []
    content_types = sorted(campaigns_df['content_type'].dropna().unique()) if 'content_type' in campaigns_df else []
    tiers = sorted(creators_df['creator_tier'].dropna().unique()) if 'creator_tier' in creators_df else []
    
    selected_creators = st.sidebar.multiselect("Creators", creators)
    selected_campaigns = st.sidebar.multiselect("Campaigns", campaign_names)
    selected_platforms = st.sidebar.multiselect("Platforms", platforms)
    selected_content = st.sidebar.multiselect("Content Types", content_types)
    selected_tiers = st.sidebar.multiselect("Creator Tiers", tiers)
    
    # Store filters
    st.session_state.filters = {
        'creators': selected_creators,
        'campaigns': selected_campaigns,
        'platforms': selected_platforms,
        'content_types': selected_content,
        'tiers': selected_tiers,
        'date_range': date_range
    }
else:
    st.sidebar.warning("Data not fully loaded.")
    st.session_state.filters = {}

pages = {
    "Dashboards": [
        st.Page("pages/overview.py", title="Executive Overview", icon=":material/dashboard:"),
        st.Page("pages/creator_analysis.py", title="Creator Performance", icon=":material/person:"),
        st.Page("pages/campaign_analysis.py", title="Campaign Analysis", icon=":material/campaign:"),
        st.Page("pages/customer_analysis.py", title="Customer Behaviour", icon=":material/groups:"),
        st.Page("pages/funnel_analysis.py", title="Funnel Analysis", icon=":material/stacked_bar_chart:"),
    ],
    "Data & Insights": [
        st.Page("pages/insights.py", title="Business Insights", icon=":material/lightbulb:"),
        st.Page("pages/data_quality.py", title="Data Quality", icon=":material/health_and_safety:"),
    ]
}

pg = st.navigation(pages)
pg.run()
