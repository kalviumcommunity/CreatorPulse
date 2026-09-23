import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.metrics import calculate_overview_kpis
from src.analytics import build_time_series, build_funnel_metrics, build_creator_metrics
from src.utils import format_currency, format_percentage, format_number
from src.page_helpers import get_filtered_data

st.title("CreatorPulse")
st.caption("Executive Overview — Real-time KPIs, trends, funnel, and creator scatter analysis")

data = get_filtered_data()
if not data:
    st.info("No records match the selected filters.", icon=":material/filter_alt_off:")
    st.stop()

try:
    kpis = calculate_overview_kpis(data)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Revenue", f"₹{format_number(kpis.get('total_revenue', 0))}")
    c2.metric("Total Orders", format_number(kpis.get('total_orders', 0)))
    c3.metric("Unique Customers", format_number(kpis.get('unique_customers', 0)))
    c4.metric("Avg Order Value", f"₹{format_number(kpis.get('aov', 0))}")
    c5.metric("Repeat Rate", format_percentage(kpis.get('repeat_purchase_rate', 0)))
    c6.metric("Acq. Cost (CAC)", f"₹{format_number(kpis.get('cac', 0))}")

    # ---- Time Series ----
    ts_df = build_time_series(data)
    if not ts_df.empty:
        st.markdown("---")
        st.subheader("Revenue & Orders Over Time", anchor=False)
        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.area(ts_df, x='month', y='revenue', title='Monthly Revenue (₹)',
                           color_discrete_sequence=['#3b82f6'])
            fig1.update_layout(xaxis_title="", yaxis_title="Revenue (₹)", template="plotly_white",
                               margin=dict(t=40, b=20))
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            fig2 = px.bar(ts_df, x='month', y='orders', title='Monthly Orders',
                          color_discrete_sequence=['#10b981'])
            fig2.update_layout(xaxis_title="", yaxis_title="Orders", template="plotly_white",
                               margin=dict(t=40, b=20))
            st.plotly_chart(fig2, use_container_width=True)

    # ---- Funnel + Scatter ----
    st.markdown("---")
    st.subheader("Acquisition Funnel & Creator Analysis", anchor=False)
    col3, col4 = st.columns([1, 1])

    with col3:
        funnel_data = build_funnel_metrics(data)
        if funnel_data:
            df_funnel = pd.DataFrame(funnel_data)
            palette = ['#1e40af', '#3b82f6', '#60a5fa', '#93c5fd', '#10b981', '#6ee7b7']
            fig_funnel = go.Figure(go.Funnel(
                y=df_funnel['stage'],
                x=df_funnel['volume'],
                textinfo="value+percent initial",
                marker={"color": palette[:len(df_funnel)]},
            ))
            fig_funnel.update_layout(title="Customer Journey Funnel", template="plotly_white",
                                     margin=dict(t=40, b=20))
            st.plotly_chart(fig_funnel, use_container_width=True)

    creator_metrics = build_creator_metrics(data)
    with col4:
        if not creator_metrics.empty and 'engagement_rate' in creator_metrics.columns:
            fig_s = px.scatter(
                creator_metrics, x="engagement_rate", y="repeat_purchase_rate",
                hover_name="creator_name", size="revenue", color="creator_tier",
                title="Engagement Rate vs Repeat Purchase Rate",
                template="plotly_white",
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig_s.update_layout(margin=dict(t=40, b=20))
            st.plotly_chart(fig_s, use_container_width=True)

except Exception as e:
    st.error(f"Error loading overview: {e}", icon=":material/error:")
