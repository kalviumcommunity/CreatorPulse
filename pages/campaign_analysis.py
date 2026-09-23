import streamlit as st
import pandas as pd
import plotly.express as px
from src.analytics import build_campaign_metrics, build_content_type_metrics
from src.utils import format_number, format_percentage
from src.page_helpers import get_filtered_data

st.title("Campaign Analysis")
st.caption("Campaign-level performance metrics, content type comparison, and ROI analysis")

data = get_filtered_data()
if not data:
    st.info("No records match the selected filters.", icon=":material/filter_alt_off:")
    st.stop()

try:
    camp_m = build_campaign_metrics(data)
    if camp_m.empty:
        st.info("No campaign data available for the selected filters.")
        st.stop()

    # ---- KPIs ----
    total_spend = camp_m['campaign_budget'].sum() if 'campaign_budget' in camp_m.columns else 0
    total_rev = camp_m['revenue'].sum() if 'revenue' in camp_m.columns else 0
    overall_roi = ((total_rev - total_spend) / total_spend * 100) if total_spend > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Campaigns", len(camp_m))
    c2.metric("Total Spend", f"₹{format_number(total_spend)}")
    c3.metric("Total Revenue", f"₹{format_number(total_rev)}")
    c4.metric("Overall ROI", format_percentage(overall_roi))

    # ---- Campaign Table ----
    st.markdown("---")
    st.subheader("Campaign Metrics", anchor=False)
    display_cols = [c for c in ['campaign_name', 'creator_name', 'platform', 'content_type',
                                 'campaign_budget', 'impressions', 'engagement_rate', 'ctr',
                                 'total_purchases', 'revenue', 'conversion_rate', 'aov', 'roi', 'cac'] if c in camp_m.columns]
    st.dataframe(
        camp_m[display_cols].style.format({
            'campaign_budget': '₹{:,.0f}', 'impressions': '{:,.0f}',
            'engagement_rate': '{:.2f}%', 'ctr': '{:.3f}%',
            'total_purchases': '{:,.0f}', 'revenue': '₹{:,.0f}',
            'conversion_rate': '{:.1f}%', 'aov': '₹{:,.0f}',
            'roi': '{:.1f}%', 'cac': '₹{:,.0f}',
        }, na_rep='—'), use_container_width=True, height=400
    )

    csv = camp_m[display_cols].to_csv(index=False)
    st.download_button("Download Campaign Metrics CSV", csv, "campaign_metrics.csv", "text/csv",
                       icon=":material/download:")

    # ---- Revenue by Campaign ----
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if 'revenue' in camp_m.columns and 'campaign_name' in camp_m.columns:
            top = camp_m.nlargest(15, 'revenue')
            fig = px.bar(top, x='revenue', y='campaign_name', orientation='h',
                         title='Top Campaigns by Revenue', color='revenue',
                         color_continuous_scale='Blues', template='plotly_white')
            fig.update_layout(yaxis_title="", xaxis_title="Revenue (₹)", margin=dict(t=40, b=20),
                              showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if 'roi' in camp_m.columns and 'campaign_name' in camp_m.columns:
            top_roi = camp_m.nlargest(15, 'roi')
            colors = ['#10b981' if v >= 0 else '#ef4444' for v in top_roi['roi']]
            fig2 = px.bar(top_roi, x='roi', y='campaign_name', orientation='h',
                          title='Campaign ROI (%)', template='plotly_white')
            fig2.update_traces(marker_color=colors)
            fig2.update_layout(yaxis_title="", xaxis_title="ROI (%)", margin=dict(t=40, b=20))
            st.plotly_chart(fig2, use_container_width=True)

    # ---- Content Type Performance ----
    st.markdown("---")
    st.subheader("Content Type Performance", anchor=False)
    ct = build_content_type_metrics(data)
    if not ct.empty:
        col3, col4 = st.columns(2)
        with col3:
            fig3 = px.bar(ct, x='content_type', y='engagement_rate',
                          title='Engagement Rate by Content Type',
                          color='content_type', template='plotly_white',
                          color_discrete_sequence=px.colors.qualitative.Set2)
            fig3.update_layout(xaxis_title="", yaxis_title="Engagement Rate (%)",
                               showlegend=False, margin=dict(t=40, b=20))
            st.plotly_chart(fig3, use_container_width=True)

        with col4:
            if 'conversion_rate' in ct.columns:
                fig4 = px.bar(ct, x='content_type', y='conversion_rate',
                              title='Conversion Rate by Content Type',
                              color='content_type', template='plotly_white',
                              color_discrete_sequence=px.colors.qualitative.Set2)
                fig4.update_layout(xaxis_title="", yaxis_title="Conversion Rate (%)",
                                   showlegend=False, margin=dict(t=40, b=20))
                st.plotly_chart(fig4, use_container_width=True)

except Exception as e:
    st.error(f"Error loading campaign analysis: {e}", icon=":material/error:")
