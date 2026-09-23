import streamlit as st
import plotly.express as px
from src.analytics import build_creator_metrics, build_campaign_metrics, build_funnel_metrics, build_creator_patterns, build_correlation_matrix
from src.insights import generate_insights
from src.page_helpers import get_filtered_data

st.title("Business Insights")
st.caption("Auto-generated strategic insights and correlations")

data = get_filtered_data()
if not data:
    st.info("No records match the selected filters.", icon=":material/filter_alt_off:")
    st.stop()

try:
    # Build dependencies
    cm = build_creator_metrics(data)
    camp_m = build_campaign_metrics(data)
    funnel = build_funnel_metrics(data)
    cp = build_creator_patterns(cm) if not cm.empty else cm

    st.subheader("Key Findings", anchor=False)
    insights = generate_insights(data, cp, camp_m, funnel)
    
    if not insights:
        st.info("Not enough data to generate insights.")
    else:
        for ins in insights:
            # Choose icon based on severity/category
            icon = "💡" # Fallback if material not parsed correctly by raw HTML, though we can use emojis purely internally here or just text
            border_color = "#3b82f6"
            if ins.get('severity') == 'High':
                icon = "⚠️"
                border_color = "#ef4444"
            elif ins.get('severity') == 'Low':
                icon = "ℹ️"
                border_color = "#10b981"
                
            st.markdown(f"""
            <div class="insight-card" style="border-left-color: {border_color};">
                <h4>{icon} {ins['title']}</h4>
                <p style="margin-bottom: 0.5rem; color: #475569;">{ins['description']}</p>
                <small style="color: #94a3b8; text-transform: uppercase;">Category: {ins.get('category', 'General')} | Severity: {ins.get('severity', 'Info')}</small>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Creator Pattern Distribution", anchor=False)
        if not cp.empty and 'pattern_label' in cp.columns:
            pattern_counts = cp['pattern_label'].value_counts().reset_index()
            pattern_counts.columns = ['Pattern', 'Count']
            fig_pie = px.pie(pattern_counts, values='Count', names='Pattern', hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Pastel,
                             template="plotly_white")
            fig_pie.update_layout(margin=dict(t=20, b=20))
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No creator pattern data available.")
            
    with col2:
        st.subheader("Metric Correlations", anchor=False)
        if not cm.empty:
            corr = build_correlation_matrix(cm)
            if not corr.empty:
                # Select a few key metrics to keep heatmap readable
                key_metrics = ['followers', 'engagement_rate', 'conversion_rate', 'repeat_purchase_rate', 'revenue', 'cac']
                avail_metrics = [m for m in key_metrics if m in corr.columns]
                if avail_metrics:
                    corr_subset = corr.loc[avail_metrics, avail_metrics]
                    fig_corr = px.imshow(corr_subset, text_auto=".2f", color_continuous_scale="RdBu_r", 
                                         aspect="auto", zmin=-1, zmax=1, template="plotly_white")
                    fig_corr.update_layout(margin=dict(t=20, b=20))
                    st.plotly_chart(fig_corr, use_container_width=True)
                else:
                    st.info("Required metrics for correlation missing.")
            else:
                st.info("Correlation matrix could not be built.")

    st.markdown("---")
    st.caption("**Disclaimer:** Correlation indicates association, not causation. All insights are generated dynamically from the underlying filtered data. Ensure sufficient sample size before making business decisions.")

except Exception as e:
    st.error(f"Error loading insights: {e}", icon=":material/error:")
