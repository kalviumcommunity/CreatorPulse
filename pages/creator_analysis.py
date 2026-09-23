import streamlit as st
import pandas as pd
import plotly.express as px
from src.analytics import build_creator_metrics, build_creator_patterns
from src.utils import format_currency, format_number, format_percentage
from src.page_helpers import get_filtered_data

st.title("Creator Performance")
st.caption("Analyse individual creator KPIs, compare creators side-by-side, and explore engagement-conversion patterns")

data = get_filtered_data()
if not data:
    st.info("No records match the selected filters.", icon=":material/filter_alt_off:")
    st.stop()

try:
    cm = build_creator_metrics(data)
    if cm.empty:
        st.info("No creator data available for the selected filters.")
        st.stop()

    cm = build_creator_patterns(cm)

    # ---- Creator Table ----
    st.subheader("Creator Metrics", anchor=False)
    display_cols = [c for c in ['creator_name', 'creator_tier', 'creator_category', 'followers',
                                 'campaign_count', 'impressions', 'engagements', 'referral_clicks',
                                 'purchases', 'revenue', 'engagement_rate', 'ctr',
                                 'conversion_rate', 'repeat_purchase_rate', 'aov', 'cac'] if c in cm.columns]
    st.dataframe(
        cm[display_cols].style.format({
            'followers': '{:,.0f}', 'impressions': '{:,.0f}', 'engagements': '{:,.0f}',
            'referral_clicks': '{:,.0f}', 'purchases': '{:,.0f}', 'revenue': '₹{:,.0f}',
            'engagement_rate': '{:.2f}%', 'ctr': '{:.3f}%', 'conversion_rate': '{:.1f}%',
            'repeat_purchase_rate': '{:.1f}%', 'aov': '₹{:,.0f}', 'cac': '₹{:,.0f}',
        }, na_rep='—'), use_container_width=True, height=400
    )

    csv = cm[display_cols].to_csv(index=False)
    st.download_button("Download Creator Metrics CSV", csv, "creator_metrics.csv", "text/csv",
                       icon=":material/download:")

    # ---- Creator Detail ----
    st.markdown("---")
    st.subheader("Creator Deep Dive", anchor=False)
    creator_names = sorted(cm['creator_name'].dropna().unique())
    selected = st.selectbox("Select a creator", creator_names)
    if selected:
        row = cm[cm['creator_name'] == selected].iloc[0]
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Revenue", f"₹{format_number(row.get('revenue', 0))}")
        c2.metric("Purchases", format_number(row.get('purchases', 0)))
        c3.metric("Eng. Rate", format_percentage(row.get('engagement_rate', 0)))
        c4.metric("Conv. Rate", format_percentage(row.get('conversion_rate', 0)))
        c5.metric("Repeat Rate", format_percentage(row.get('repeat_purchase_rate', 0)))

        if 'pattern_label' in row.index:
            st.info(f"**Creator Pattern:** {row['pattern_label']}", icon=":material/label:")

    # ---- Comparison ----
    st.markdown("---")
    st.subheader("Creator Comparison", anchor=False)
    compare = st.multiselect("Select 2–4 creators to compare", creator_names, max_selections=4)
    if len(compare) >= 2:
        comp_df = cm[cm['creator_name'].isin(compare)]
        comp_cols = [c for c in ['creator_name', 'revenue', 'purchases', 'engagement_rate',
                                  'conversion_rate', 'repeat_purchase_rate', 'cac'] if c in comp_df.columns]
        st.dataframe(comp_df[comp_cols].style.format({
            'revenue': '₹{:,.0f}', 'purchases': '{:,.0f}',
            'engagement_rate': '{:.2f}%', 'conversion_rate': '{:.1f}%',
            'repeat_purchase_rate': '{:.1f}%', 'cac': '₹{:,.0f}',
        }, na_rep='—'), use_container_width=True)

    # ---- Quadrant Plot ----
    st.markdown("---")
    st.subheader("Engagement–Conversion Quadrant", anchor=False)
    if 'engagement_rate' in cm.columns and 'repeat_purchase_rate' in cm.columns:
        eng_med = cm['engagement_rate'].median()
        conv_med = cm['repeat_purchase_rate'].median()

        fig = px.scatter(
            cm, x='engagement_rate', y='repeat_purchase_rate',
            hover_name='creator_name', size='revenue', color='pattern_label' if 'pattern_label' in cm.columns else 'creator_tier',
            title="Quadrant: Engagement Rate vs Repeat Purchase Rate",
            template="plotly_white", color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.add_hline(y=conv_med, line_dash="dash", line_color="#94a3b8", annotation_text=f"Median RPR ({conv_med:.1f}%)")
        fig.add_vline(x=eng_med, line_dash="dash", line_color="#94a3b8", annotation_text=f"Median Eng ({eng_med:.1f}%)")
        fig.update_layout(margin=dict(t=50, b=20))
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Error loading creator analysis: {e}", icon=":material/error:")
