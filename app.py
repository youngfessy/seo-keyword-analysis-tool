import streamlit as st

# Configure page - MUST be first Streamlit command
st.set_page_config(
    page_title="SEO Analysis Suite",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for unified app styling
st.markdown("""
<style>
    /* Dark mode table styling */
    .stDataFrame > div {
        background-color: #1e1e1e !important;
        color: #ffffff !important;
    }
    
    .stDataFrame table {
        background-color: #1e1e1e !important;
        color: #ffffff !important;
    }
    
    .stDataFrame th {
        background-color: #2d2d2d !important;
        color: #ffffff !important;
        border: 1px solid #404040 !important;
    }
    
    .stDataFrame td {
        background-color: #1e1e1e !important;
        color: #ffffff !important;
        border: 1px solid #404040 !important;
    }
    
    /* High priority rows */
    .priority-high {
        background-color: #4a1a1a !important;
        color: #ffffff !important;
    }
    
    /* Medium priority rows */
    .priority-medium {
        background-color: #4a3a1a !important;
        color: #ffffff !important;
    }
    
    /* Low priority rows */
    .priority-low {
        background-color: #1a4a1a !important;
        color: #ffffff !important;
    }
    
    /* AEO/GEO specific styling */
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #4CAF50;
    }
    
    .stDataFrame {
        border-radius: 0.5rem;
    }
    
    .stTab {
        font-size: 1.1rem;
        font-weight: 600;
    }
    
    /* Main content area */
    .main .block-container {
        padding-top: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: none;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

import sys
import os

# Add current directory to path so we can import our modules
sys.path.append(os.path.dirname(__file__))

# Import the dashboard functions
from dashboard import main as seo_main, display_glossary as seo_glossary
from aeo_geo_dashboard import main as aeo_main

def main():
    """Main application with navigation between SEO and AEO/GEO dashboards."""
    
    # Sidebar navigation
    st.sidebar.title("📊 SEO Analysis Suite")
    st.sidebar.markdown("**synthesis.com/tutor**")
    st.sidebar.markdown("---")
    
    # Page selection
    page = st.sidebar.selectbox(
        "Choose Dashboard:",
        ["🎯 SEO Opportunities", "🤖 AEO/GEO Analysis"],
        index=0
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.markdown("""
    **SEO Opportunities**: Keyword ranking analysis with optimization recommendations
    
    **AEO/GEO Analysis**: Answer Engine & Generative Engine optimization for featured snippets and AI responses
    """)
    
    # Route to selected page
    if page == "🎯 SEO Opportunities":
        # Remove the navigation section from the original function since we're handling it here
        seo_dashboard()
    elif page == "🤖 AEO/GEO Analysis":
        # Remove the navigation section from the original function since we're handling it here  
        aeo_dashboard()

def seo_dashboard():
    """SEO dashboard without navigation sidebar."""
    # Import the functions we need from dashboard.py
    from dashboard import (
        load_latest_data, create_summary_metrics, create_visualizations,
        filter_dataframe, display_paginated_table, export_filtered_data,
        display_glossary
    )
    from datetime import datetime
    
    # Header
    st.title("🎯 SEO Keyword Opportunities Dashboard")
    st.markdown("### synthesis.com/tutor - Keyword Analysis")
    
    # Load data
    df, filename = load_latest_data()
    
    if df is None:
        st.error("No keyword opportunities data found. Please run the keyword analyzer first.")
        st.code("python3 keyword_analyzer.py")
        return
    
    # Show data source info
    if filename == "live_gsc_data":
        st.info(f"📊 Data loaded from: **Live Google Search Console** | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.info(f"📊 Data loaded from: **{filename}** | Last updated: {datetime.fromtimestamp(os.path.getctime(filename)).strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Summary metrics
    create_summary_metrics(df)
    
    # Visualizations
    st.markdown("---")
    create_visualizations(df)
    
    # Filters and table
    st.markdown("---")
    filtered_df = filter_dataframe(df)
    
    if len(filtered_df) == 0:
        st.warning("No keywords match your current filters. Please adjust the filter criteria.")
        return
    
    # Show filtered results count
    if len(filtered_df) != len(df):
        st.success(f"🔍 Showing {len(filtered_df)} keywords (filtered from {len(df)} total)")
    
    # Display paginated table with deletion functionality
    displayed_df = display_paginated_table(filtered_df, filename)
    
    # Export functionality
    export_filtered_data(filtered_df)
    
    # Quick insights - updated to reflect current filtered data
    st.markdown("---")
    st.subheader("🚀 Quick Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Top 5 Opportunities:**")
        top_5 = filtered_df.nlargest(5, 'Opportunity Score')[['Keyword', 'Current Position', 'Opportunity Score', 'Opportunity Type', 'Keyword Difficulty']]
        for idx, row in top_5.iterrows():
            st.write(f"• **{row['Keyword']}** (Pos {row['Current Position']:.1f}, Score {row['Opportunity Score']:.1f}, KD {row['Keyword Difficulty']})")
    
    with col2:
        st.markdown("**Highest Traffic Potential:**")
        top_traffic = filtered_df.nlargest(5, 'Traffic Potential')[['Keyword', 'Traffic Potential', 'Current Position', 'Search Intent']]
        for idx, row in top_traffic.iterrows():
            st.write(f"• **{row['Keyword']}** (+{row['Traffic Potential']:,} clicks, Pos {row['Current Position']:.1f}, {row['Search Intent']})")

    # Glossary
    display_glossary()

def aeo_dashboard():
    """AEO/GEO dashboard without navigation sidebar."""
    # Import the functions we need from aeo_geo_dashboard.py
    from aeo_geo_dashboard import (
        get_aeo_data_from_session, create_summary_metrics, create_visualizations,
        display_analysis_table, display_insights, display_glossary
    )
    
    # Header
    st.title("🤖 AEO/GEO Analysis Dashboard")
    st.markdown("### Answer Engine & Generative Engine Optimization for synthesis.com/tutor")
    
    # Initialize session state for data caching
    if 'aeo_data_loaded' not in st.session_state:
        st.session_state.aeo_data_loaded = False
        st.session_state.aeo_data = None
    
    # Load data only once or when explicitly refreshed
    if not st.session_state.aeo_data_loaded or st.session_state.aeo_data is None:
        df = get_aeo_data_from_session()
        if df is not None and len(df) > 0:
            st.session_state.aeo_data = df
            st.session_state.aeo_data_loaded = True
    else:
        df = st.session_state.aeo_data
    
    if df is None or len(df) == 0:
        st.error("Unable to fetch data from Google Search Console. Please check your connection and authentication.")
        return
    
    # Add refresh button and data info
    col1, col2 = st.columns([3, 1])
    with col1:
        st.success(f"✅ Loaded {len(df):,} non-brand queries for AEO/GEO analysis")
    with col2:
        if st.button("🔄 Refresh Data", help="Reload data from Google Search Console"):
            st.session_state.aeo_data_loaded = False
            st.session_state.aeo_data = None
            st.cache_data.clear()  # Clear Streamlit cache
            st.rerun()

    # Summary metrics
    create_summary_metrics(df)
    
    # Visualizations
    st.markdown("---")
    create_visualizations(df)
    
    # Analysis table
    st.markdown("---")
    filtered_df = display_analysis_table(df)
    
    # Insights
    display_insights(filtered_df)
    
    # Glossary
    display_glossary()

if __name__ == "__main__":
    main() 