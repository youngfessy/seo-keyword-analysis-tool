#!/usr/bin/env python3
"""
Multi-Dashboard for SEO, AEO, and GEO Analysis

Comprehensive Streamlit dashboard with multiple tabs for:
- SEO: Traditional keyword opportunity analysis
- AEO/GEO: Answer Engine and Generative Engine Optimization
"""

import streamlit as st
import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import re

# Page configuration
st.set_page_config(
    page_title="SEO/AEO/GEO Analysis Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import GSC client
try:
    from gsc_client import GSCClient
    from config import Config
except ImportError:
    st.error("Required modules not found. Make sure gsc_client.py and config.py are in the same directory.")
    st.stop()

# Custom CSS for styling
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
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #262730;
        border-radius: 5px 5px 0 0;
        color: white;
        font-size: 16px;
        font-weight: bold;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

def format_large_number(num):
    """Format large numbers with K, M suffixes."""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    else:
        return str(int(num))

def classify_aeo_geo_intent(keyword):
    """Classify keyword for AEO/GEO analysis."""
    keyword_lower = keyword.lower()
    
    # Question-based queries (high AEO potential)
    if any(starter in keyword_lower for starter in ['how', 'what', 'why', 'when', 'where', 'who', 'which']):
        return 'Question-Based'
    
    # Definition queries
    if any(term in keyword_lower for term in ['define', 'definition', 'meaning', 'what is', 'what does']):
        return 'Definition'
    
    # Comparison queries
    if any(term in keyword_lower for term in ['vs', 'versus', 'compare', 'difference', 'better']):
        return 'Comparison'
    
    # How-to queries
    if any(term in keyword_lower for term in ['how to', 'tutorial', 'guide', 'step by step']):
        return 'How-To'
    
    # List queries
    if any(term in keyword_lower for term in ['list', 'examples', 'types of', 'kinds of']):
        return 'List-Based'
    
    # Factual queries
    return 'Factual'

def analyze_serp_features(keyword):
    """Estimate SERP feature potential based on keyword characteristics."""
    keyword_lower = keyword.lower()
    features = []
    
    # Featured snippet potential
    if any(starter in keyword_lower for starter in ['how', 'what', 'why', 'when', 'where']):
        features.append('Featured Snippet')
    
    # FAQ potential
    if any(term in keyword_lower for term in ['faq', 'questions', 'common', 'frequently']):
        features.append('FAQ')
    
    # How-to potential
    if any(term in keyword_lower for term in ['how to', 'tutorial', 'guide']):
        features.append('How-To')
    
    # Knowledge panel potential
    if any(term in keyword_lower for term in ['what is', 'define', 'definition']):
        features.append('Knowledge Panel')
    
    return features if features else ['Standard Results']

def get_expected_ctr(position):
    """Get expected CTR based on position."""
    ctr_by_position = {
        1: 0.31, 2: 0.24, 3: 0.18, 4: 0.13, 5: 0.09,
        6: 0.06, 7: 0.04, 8: 0.03, 9: 0.025, 10: 0.02
    }
    pos = min(10, max(1, round(position)))
    return ctr_by_position.get(pos, 0.01)

def calculate_answer_potential(row):
    """Calculate answer optimization potential score."""
    score = 0
    
    # Base score from CTR gap
    expected_ctr = get_expected_ctr(row['position'])
    ctr_gap = expected_ctr - row['ctr']
    score += (ctr_gap * 100) * 0.4  # 40% weight
    
    # Question-based bonus
    if row['Question_Based']:
        score += 20
    
    # High impression bonus
    if row['impressions'] > 1000:
        score += 15
    elif row['impressions'] > 100:
        score += 10
    
    # Position bonus (closer to featured snippet territory)
    if row['position'] <= 5:
        score += 15
    elif row['position'] <= 10:
        score += 10
    
    # Length bonus (longer queries often need answers)
    if len(row['query']) > 30:
        score += 10
    
    return min(100, max(0, score))

@st.cache_data
def load_latest_seo_data():
    """Load the latest SEO keyword opportunities data."""
    csv_files = glob.glob("keyword_opportunities_*.csv")
    if not csv_files:
        return None, None
    
    latest_file = max(csv_files, key=os.path.getctime)
    df = pd.read_csv(latest_file)
    return df, latest_file

@st.cache_data
def fetch_aeo_geo_data():
    """Fetch and analyze GSC data for AEO/GEO optimization."""
    try:
        config = Config()
        gsc_client = GSCClient()
        gsc_client.authenticate()
        
        # Fetch data from last 90 days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=90)
        
        # Get search analytics data
        search_analytics = gsc_client.get_search_analytics(
            site_url=config.TARGET_DOMAIN,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            dimensions=['query'],
            row_limit=5000
        )
        
        if not search_analytics:
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(search_analytics)
        
        # Filter for non-brand keywords
        brand_keywords = config.BRAND_KEYWORDS
        brand_pattern = '|'.join([re.escape(brand.lower()) for brand in brand_keywords])
        df_filtered = df[~df['query'].str.lower().str.contains(brand_pattern, na=False)]
        
        # Add AEO/GEO analysis columns
        df_filtered['AEO_GEO_Intent'] = df_filtered['query'].apply(classify_aeo_geo_intent)
        df_filtered['SERP_Features'] = df_filtered['query'].apply(analyze_serp_features)
        df_filtered['Question_Based'] = df_filtered['query'].str.lower().str.contains('how|what|why|when|where|who', na=False)
        df_filtered['Answer_Potential'] = df_filtered.apply(calculate_answer_potential, axis=1)
        
        return df_filtered
        
    except Exception as e:
        st.error(f"Error fetching AEO/GEO data: {str(e)}")
        return None

def create_seo_summary_metrics(df):
    """Create summary metrics cards for SEO."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Keywords",
            value=format_large_number(len(df)),
            delta=None
        )
    
    with col2:
        high_priority = len(df[df['Priority'] == 'High'])
        st.metric(
            label="High Priority",
            value=format_large_number(high_priority),
            delta=f"{high_priority/len(df)*100:.1f}% of total"
        )
    
    with col3:
        total_traffic_potential = df['Traffic Potential'].sum()
        st.metric(
            label="Traffic Potential",
            value=format_large_number(total_traffic_potential),
            delta="Additional monthly clicks"
        )
    
    with col4:
        avg_score = df['Opportunity Score'].mean()
        st.metric(
            label="Avg Opportunity Score",
            value=f"{avg_score:.1f}",
            delta=f"Out of 100"
        )

def create_seo_visualizations(df):
    """Create dashboard visualizations for SEO."""
    col1, col2 = st.columns(2)
    
    with col1:
        # Priority breakdown pie chart
        priority_counts = df['Priority'].value_counts()
        fig_pie = px.pie(
            values=priority_counts.values,
            names=priority_counts.index,
            title="Keywords by Priority Level",
            color_discrete_map={
                'High': '#ff4b4b',
                'Medium': '#ffa500', 
                'Low': '#87ceeb'
            }
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Search intent breakdown
        intent_counts = df['Search Intent'].value_counts()
        fig_bar = px.bar(
            x=intent_counts.values,
            y=intent_counts.index,
            orientation='h',
            title="Keywords by Search Intent",
            labels={'x': 'Number of Keywords', 'y': 'Search Intent'},
            color=intent_counts.values,
            color_continuous_scale='viridis'
        )
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)

def create_aeo_geo_summary_metrics(df):
    """Create summary metrics for AEO/GEO analysis."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        question_queries = len(df[df['Question_Based'] == True])
        st.metric(
            label="Question-Based Queries",
            value=format_large_number(question_queries),
            delta=f"{question_queries/len(df)*100:.1f}% of total"
        )
    
    with col2:
        high_answer_potential = len(df[df['Answer_Potential'] >= 70])
        st.metric(
            label="High Answer Potential",
            value=format_large_number(high_answer_potential),
            delta="Optimization targets"
        )
    
    with col3:
        avg_position = df['position'].mean()
        st.metric(
            label="Avg Position",
            value=f"{avg_position:.1f}",
            delta="All queries"
        )
    
    with col4:
        total_impressions = df['impressions'].sum()
        st.metric(
            label="Total Impressions",
            value=format_large_number(total_impressions),
            delta="90 days"
        )

def create_aeo_geo_visualizations(df):
    """Create visualizations for AEO/GEO analysis."""
    col1, col2 = st.columns(2)
    
    with col1:
        # AEO/GEO Intent breakdown
        intent_counts = df['AEO_GEO_Intent'].value_counts()
        fig_pie = px.pie(
            values=intent_counts.values,
            names=intent_counts.index,
            title="Query Types for AEO/GEO",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Answer potential distribution
        potential_bins = pd.cut(df['Answer_Potential'], 
                              bins=[0, 30, 60, 80, 100], 
                              labels=['Low (0-30)', 'Medium (31-60)', 'High (61-80)', 'Very High (81-100)'])
        potential_counts = potential_bins.value_counts()
        
        fig_bar = px.bar(
            x=potential_counts.index,
            y=potential_counts.values,
            title="Answer Optimization Potential Distribution",
            labels={'x': 'Potential Level', 'y': 'Number of Queries'},
            color=potential_counts.values,
            color_continuous_scale='RdYlGn'
        )
        st.plotly_chart(fig_bar, use_container_width=True)

def display_aeo_geo_table(df):
    """Display AEO/GEO analysis table with filtering."""
    st.subheader("🤖 AEO/GEO Query Analysis")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        intent_filter = st.selectbox(
            "Query Intent",
            ['All'] + list(df['AEO_GEO_Intent'].unique())
        )
    
    with col2:
        question_filter = st.selectbox(
            "Question-Based",
            ['All', 'Yes', 'No']
        )
    
    with col3:
        min_potential = st.slider(
            "Min Answer Potential",
            min_value=0,
            max_value=100,
            value=50,
            step=5
        )
    
    # Apply filters
    filtered_df = df.copy()
    
    if intent_filter != 'All':
        filtered_df = filtered_df[filtered_df['AEO_GEO_Intent'] == intent_filter]
    
    if question_filter == 'Yes':
        filtered_df = filtered_df[filtered_df['Question_Based'] == True]
    elif question_filter == 'No':
        filtered_df = filtered_df[filtered_df['Question_Based'] == False]
    
    filtered_df = filtered_df[filtered_df['Answer_Potential'] >= min_potential]
    
    # Sort by answer potential
    filtered_df = filtered_df.sort_values('Answer_Potential', ascending=False)
    
    # Display table
    display_df = filtered_df[['query', 'impressions', 'clicks', 'ctr', 'position', 
                             'AEO_GEO_Intent', 'Question_Based', 'Answer_Potential', 'SERP_Features']].copy()
    
    # Format columns
    display_df['ctr'] = display_df['ctr'].apply(lambda x: f"{x:.3f}")
    display_df['position'] = display_df['position'].apply(lambda x: f"{x:.1f}")
    display_df['Answer_Potential'] = display_df['Answer_Potential'].apply(lambda x: f"{x:.1f}")
    
    # Column configuration
    column_config = {
        "query": st.column_config.TextColumn("Query", width="medium"),
        "impressions": st.column_config.NumberColumn("Impressions", format="%d"),
        "clicks": st.column_config.NumberColumn("Clicks", format="%d"),
        "ctr": st.column_config.TextColumn("CTR", width="small"),
        "position": st.column_config.TextColumn("Position", width="small"),
        "AEO_GEO_Intent": st.column_config.TextColumn("Intent", width="medium"),
        "Question_Based": st.column_config.CheckboxColumn("Question?", width="small"),
        "Answer_Potential": st.column_config.TextColumn("Answer Potential", width="small"),
        "SERP_Features": st.column_config.ListColumn("SERP Features", width="medium")
    }
    
    st.dataframe(
        display_df,
        use_container_width=True,
        column_config=column_config,
        hide_index=True
    )
    
    return filtered_df

def display_aeo_geo_glossary():
    """Display AEO/GEO glossary."""
    st.markdown("---")
    st.header("📖 AEO/GEO Glossary & Definitions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Query Intent Types")
        st.markdown("""
        **Question-Based**: Queries starting with how, what, why, when, where, who. High potential for featured snippets and voice search.
        
        **Definition**: Queries seeking explanations of terms or concepts. Perfect for knowledge panels and answer boxes.
        
        **Comparison**: Queries comparing options (vs, versus, compare). Ideal for comparison tables and structured content.
        
        **How-To**: Instructional queries requiring step-by-step guidance. Great for tutorial content and rich snippets.
        
        **List-Based**: Queries seeking lists or examples. Perfect for structured list content and numbered snippets.
        
        **Factual**: Direct factual queries requiring concise answers.
        """)
    
    with col2:
        st.subheader("SERP Features & Optimization")
        st.markdown("""
        **Featured Snippet**: The "position zero" answer box. Optimize with clear, concise answers in 40-60 words.
        
        **FAQ**: Frequently Asked Questions sections. Use FAQ schema markup and natural question formats.
        
        **How-To**: Step-by-step instructions. Use ordered lists and how-to schema markup.
        
        **Knowledge Panel**: Entity information boxes. Focus on E-A-T signals and entity optimization.
        
        **Answer Potential Score**: Calculated based on CTR gap, question format, impressions, position, and query length. Higher scores indicate better optimization opportunities.
        """)
    
    st.subheader("AEO vs GEO Optimization")
    st.markdown("""
    **AEO (Answer Engine Optimization)**: Optimizing for traditional search engines' answer features like featured snippets, knowledge panels, and voice search results.
    
    **GEO (Generative Engine Optimization)**: Optimizing for AI-powered search engines and chatbots like ChatGPT, Bard, and Bing Chat that generate direct answers.
    
    **Key Differences:**
    - **AEO**: Focus on structured data, clear headings, concise answers, FAQ formats
    - **GEO**: Focus on comprehensive content, context, authority signals, and natural language
    """)

def main():
    """Main dashboard function with tabs."""
    # Header
    st.title("🎯 Comprehensive SEO/AEO/GEO Analysis Dashboard")
    st.markdown("### synthesis.com/tutor - Multi-Channel Search Optimization")
    
    # Create tabs
    tab1, tab2 = st.tabs(["🔍 SEO Analysis", "🤖 AEO/GEO Analysis"])
    
    with tab1:
        st.header("SEO Keyword Opportunities")
        
        # Load SEO data
        seo_df, filename = load_latest_seo_data()
        
        if seo_df is None:
            st.error("No SEO keyword opportunities data found. Please run the keyword analyzer first.")
            st.code("python3 keyword_analyzer.py")
        else:
            # Show data source info
            st.info(f"📊 Data loaded from: **{filename}** | Last updated: {datetime.fromtimestamp(os.path.getctime(filename)).strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Summary metrics
            create_seo_summary_metrics(seo_df)
            
            # Visualizations
            st.markdown("---")
            create_seo_visualizations(seo_df)
            
            # Top opportunities preview
            st.markdown("---")
            st.subheader("🚀 Top SEO Opportunities (Preview)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Top 5 Opportunities:**")
                top_5 = seo_df.nlargest(5, 'Opportunity Score')[['Keyword', 'Current Position', 'Opportunity Score', 'Priority']]
                for idx, row in top_5.iterrows():
                    st.write(f"• **{row['Keyword']}** (Pos {row['Current Position']:.1f}, Score {row['Opportunity Score']:.1f})")
            
            with col2:
                st.markdown("**Highest Traffic Potential:**")
                top_traffic = seo_df.nlargest(5, 'Traffic Potential')[['Keyword', 'Traffic Potential', 'Current Position']]
                for idx, row in top_traffic.iterrows():
                    st.write(f"• **{row['Keyword']}** (+{row['Traffic Potential']:,} clicks, Pos {row['Current Position']:.1f})")
            
            # Note about full SEO dashboard
            st.info("💡 **Note**: This is a summary view. For full SEO analysis with filtering, sorting, and keyword management, use: `streamlit run dashboard.py`")
    
    with tab2:
        st.header("AEO/GEO Query Analysis")
        st.markdown("**Answer Engine Optimization & Generative Engine Optimization**")
        
        # Load AEO/GEO data
        with st.spinner("🔍 Fetching Google Search Console data for AEO/GEO analysis..."):
            aeo_geo_df = fetch_aeo_geo_data()
        
        if aeo_geo_df is None:
            st.error("Unable to fetch AEO/GEO data from Google Search Console.")
        else:
            st.success(f"✅ Loaded {len(aeo_geo_df)} queries for AEO/GEO analysis")
            
            # Summary metrics
            create_aeo_geo_summary_metrics(aeo_geo_df)
            
            # Visualizations
            st.markdown("---")
            create_aeo_geo_visualizations(aeo_geo_df)
            
            # Interactive table
            st.markdown("---")
            filtered_aeo_df = display_aeo_geo_table(aeo_geo_df)
            
            # Insights
            st.markdown("---")
            st.subheader("🚀 AEO/GEO Optimization Insights")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Top Question-Based Opportunities:**")
                question_ops = filtered_aeo_df[filtered_aeo_df['Question_Based'] == True].nlargest(5, 'Answer_Potential')
                for idx, row in question_ops.iterrows():
                    st.write(f"• **{row['query']}** (Potential: {row['Answer_Potential']:.1f}, Pos: {row['position']:.1f})")
            
            with col2:
                st.markdown("**High-Impression Answer Targets:**")
                high_impression = filtered_aeo_df.nlargest(5, 'impressions')
                for idx, row in high_impression.iterrows():
                    st.write(f"• **{row['query']}** ({row['impressions']:,} impressions, {row['AEO_GEO_Intent']})")
            
            # Glossary
            display_aeo_geo_glossary()

if __name__ == "__main__":
    main() 