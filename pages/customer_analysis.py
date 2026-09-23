import streamlit as st
import pandas as pd
import plotly.express as px
from src.analytics import build_customer_metrics, build_cohort_analysis
from src.utils import format_number, format_percentage
from src.page_helpers import get_filtered_data

st.title("Customer Behaviour")
st.caption("Customer segmentation, purchase frequency, revenue distribution, and cohort retention")

data = get_filtered_data()
if not data:
    st.info("No records match the selected filters.", icon=":material/filter_alt_off:")
    st.stop()

try:
    cust = build_customer_metrics(data)
    if not cust:
        st.info("No customer data available for the selected filters.")
        st.stop()

    # ---- KPIs ----
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Unique Customers", format_number(cust.get('unique_customers', 0)))
    c2.metric("One-time", format_number(cust.get('one_time', 0)))
    c3.metric("Repeat", format_number(cust.get('repeat', 0)))
    c4.metric("High-value", format_number(cust.get('high_value', 0)))
    c5.metric("Avg Orders/Customer", f"{cust.get('avg_orders_per_customer', 0):.2f}")
    c6.metric("Avg Revenue/Customer", f"₹{format_number(cust.get('avg_revenue_per_customer', 0))}")

    threshold = cust.get('high_value_threshold', 0)
    if threshold > 0:
        st.caption(f"High-value threshold (top 20%): ₹{threshold:,.0f} lifetime spend")

    st.markdown("---")
    col1, col2 = st.columns(2)

    # ---- Frequency Distribution ----
    with col1:
        freq = cust.get('frequency_distribution', {})
        if freq:
            df_freq = pd.DataFrame({'Purchases': list(freq.keys()), 'Customers': list(freq.values())})
            fig1 = px.bar(df_freq, x='Purchases', y='Customers',
                          title='Purchase Frequency Distribution',
                          color_discrete_sequence=['#3b82f6'], template='plotly_white')
            fig1.update_layout(xaxis_title="Number of Purchases", yaxis_title="Customers",
                               margin=dict(t=40, b=20))
            st.plotly_chart(fig1, use_container_width=True)

    # ---- Segment Pie ----
    with col2:
        seg = cust.get('segment_counts', {})
        if seg:
            df_seg = pd.DataFrame({'Segment': list(seg.keys()), 'Count': list(seg.values())})
            colors = {'One-time': '#94a3b8', 'Repeat': '#3b82f6', 'High-value': '#10b981'}
            fig2 = px.pie(df_seg, values='Count', names='Segment',
                          title='Customer Segments',
                          color='Segment', color_discrete_map=colors,
                          template='plotly_white')
            fig2.update_layout(margin=dict(t=40, b=20))
            st.plotly_chart(fig2, use_container_width=True)

    # ---- Revenue Distribution ----
    st.markdown("---")
    cust_data = cust.get('customer_data', pd.DataFrame())
    if not cust_data.empty and 'total_spent' in cust_data.columns:
        col3, col4 = st.columns(2)
        with col3:
            fig3 = px.histogram(cust_data, x='total_spent', nbins=30,
                                title='Customer Revenue Distribution',
                                color_discrete_sequence=['#6366f1'], template='plotly_white')
            fig3.update_layout(xaxis_title="Total Spend (₹)", yaxis_title="Customers",
                               margin=dict(t=40, b=20))
            st.plotly_chart(fig3, use_container_width=True)

        with col4:
            fig4 = px.histogram(cust_data, x='order_count', nbins=10,
                                title='Orders per Customer Distribution',
                                color_discrete_sequence=['#f59e0b'], template='plotly_white')
            fig4.update_layout(xaxis_title="Orders", yaxis_title="Customers",
                               margin=dict(t=40, b=20))
            st.plotly_chart(fig4, use_container_width=True)

    # ---- Cohort Analysis ----
    st.markdown("---")
    st.subheader("Cohort Retention", anchor=False)
    cohort = build_cohort_analysis(data)
    if not cohort.empty:
        # Normalize to percentages
        cohort_pct = cohort.div(cohort.iloc[:, 0], axis=0) * 100
        cohort_pct = cohort_pct.round(1)
        cohort_pct.index = cohort_pct.index.astype(str)
        cohort_pct.columns = [f"Month {c}" for c in cohort_pct.columns]

        fig5 = px.imshow(cohort_pct, text_auto=True,
                         title='Cohort Retention Heatmap (%)',
                         color_continuous_scale='Blues', aspect='auto',
                         labels=dict(x="Months Since First Purchase", y="Cohort Month", color="Retention %"))
        fig5.update_layout(margin=dict(t=40, b=20))
        st.plotly_chart(fig5, use_container_width=True)
    else:
        st.info("Insufficient data for cohort analysis.")

except Exception as e:
    st.error(f"Error loading customer analysis: {e}", icon=":material/error:")
