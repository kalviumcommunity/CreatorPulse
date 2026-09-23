import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.analytics import build_funnel_metrics
from src.page_helpers import get_filtered_data

st.title("Funnel Analysis")
st.caption("Detailed view of user journey from impressions to repeat purchases")

data = get_filtered_data()
if not data:
    st.info("No records match the selected filters.", icon=":material/filter_alt_off:")
    st.stop()

try:
    funnel_data = build_funnel_metrics(data)
    if not funnel_data:
        st.info("No funnel data available for the selected filters.")
        st.stop()

    df_funnel = pd.DataFrame(funnel_data)
    
    # Funnel Chart
    palette = ['#1e40af', '#3b82f6', '#60a5fa', '#93c5fd', '#10b981', '#6ee7b7']
    fig = go.Figure(go.Funnel(
        y=df_funnel['stage'],
        x=df_funnel['volume'],
        textinfo="value+percent initial",
        marker={"color": palette[:len(df_funnel)]}
    ))
    fig.update_layout(title="Complete Customer Journey", template="plotly_white", margin=dict(t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)

    # Breakdown Table
    st.subheader("Funnel Breakdown", anchor=False)
    st.dataframe(
        df_funnel.style.format({
            'volume': '{:,.0f}',
            'pct_of_previous': '{:.1f}%',
            'dropoff_pct': '{:.1f}%'
        }), 
        use_container_width=True,
        hide_index=True
    )

    # Find biggest dropoff
    if len(df_funnel) > 1:
        dropoffs = df_funnel.iloc[1:] # Skip first stage
        max_drop = dropoffs.loc[dropoffs['dropoff_pct'].idxmax()]
        st.info(f"**Biggest Drop-off**: {max_drop['stage']} at {max_drop['dropoff_pct']:.1f}%", icon=":material/trending_down:")

except Exception as e:
    st.error(f"Error loading funnel analysis: {e}", icon=":material/error:")
