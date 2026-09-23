import streamlit as st
import pandas as pd
from src.validation import generate_validation_report, profile_dataset
from src.page_helpers import get_filtered_data

st.title("Data Quality")
st.caption("System health, validation rules, and data profiling metrics")

data = get_filtered_data()
if not data:
    st.info("No records match the selected filters.", icon=":material/filter_alt_off:")
    st.stop()

try:
    st.subheader("Validation Report", anchor=False)
    report = generate_validation_report(data)
    
    if report:
        df_report = pd.DataFrame(report)
        # Map boolean status to icons
        df_report['status_icon'] = df_report['status'].apply(lambda x: "✅ Pass" if x else "⚠️ Warning")
        
        # Reorder columns for display
        df_report = df_report[['status_icon', 'check', 'details']]
        df_report.columns = ['Status', 'Check', 'Details']
        
        st.dataframe(df_report, use_container_width=True, hide_index=True)
    else:
        st.info("No validation rules configured.")

    st.markdown("---")
    st.subheader("Dataset Profiling", anchor=False)
    
    tabs = st.tabs(list(data.keys()))
    
    for tab, (name, df) in zip(tabs, data.items()):
        with tab:
            profile = profile_dataset(df, name)
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Rows", f"{profile['rows']:,}")
            col2.metric("Columns", f"{profile['columns']:,}")
            col3.metric("Missing %", f"{profile['total_missing_pct']:.2f}%")
            col4.metric("Duplicates", f"{profile['duplicates']:,}")
            
            st.markdown("**Columns:**")
            st.write(", ".join(profile['column_names']))
            
            if profile.get('date_ranges'):
                st.markdown("**Date Ranges:**")
                for col, d_range in profile['date_ranges'].items():
                    st.write(f"- `{col}`: {d_range}")

except Exception as e:
    st.error(f"Error loading data quality report: {e}", icon=":material/error:")
