#!/usr/bin/env python3
"""
AEO/GEO Dashboard - Answer Engine & Generative Engine Optimization

Standalone Streamlit dashboard for analyzing keyword opportunities
specifically for Answer Engines (featured snippets, voice search) 
and Generative Engines (AI chatbots, generative search).
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import re
import os

# Page configuration will be handled by main app

# Import existing modules
try:
    from gsc_client import GSCClient
    import config
except ImportError as e:
    st.error(f"Required modules not found: {e}")
    st.stop()

# Custom CSS for clean styling
st.markdown("""
<style>
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
</style>
""", unsafe_allow_html=True)

def classify_aeo_geo_intent(keyword):
    """Classify keyword intent for AEO/GEO analysis."""
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
    
    return 'Factual'

def analyze_serp_features(keyword):
    """Identify SERP feature opportunities."""
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

def estimate_search_volume(keyword, impressions):
    """Get real search volume from Ahrefs with fallback to impressions estimate."""
    from ahrefs_data_loader import get_real_search_volume
    return get_real_search_volume(keyword, impressions)

def calculate_answer_potential(row):
    """Calculate optimization potential for answer engines."""
    score = 0
    
    # Position factor (40% weight) - higher positions = better foundation
    position_score = max(0, (21 - min(20, row['position'])) / 20) * 100
    score += position_score * 0.4
    
    # Volume factor (30% weight) - more impressions = more opportunity
    volume_score = min(np.log10(max(1, row['impressions'])) / 4, 1) * 100
    score += volume_score * 0.3
    
    # Question format bonus (20% weight)
    keyword_lower = row['query'].lower()
    if any(starter in keyword_lower for starter in ['how', 'what', 'why', 'when', 'where', 'who']):
        question_score = 100
    else:
        question_score = 50
    score += question_score * 0.2
    
    # Length factor (10% weight) - longer queries often better for answers
    if len(row['query'].split()) >= 4:
        length_score = 100
    elif len(row['query'].split()) >= 3:
        length_score = 70
    else:
        length_score = 40
    score += length_score * 0.1
    
    return min(100, max(0, score))

def load_deleted_keywords():
    """Load permanently deleted keywords from file."""
    deleted_file = "deleted_aeo_keywords.txt"
    if os.path.exists(deleted_file):
        with open(deleted_file, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_deleted_keywords(deleted_keywords):
    """Save permanently deleted keywords to file."""
    deleted_file = "deleted_aeo_keywords.txt"
    with open(deleted_file, 'w') as f:
        for keyword in sorted(deleted_keywords):
            f.write(f"{keyword}\n")

@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_raw_gsc_data(start_date_str, end_date_str):
    """Fetch raw GSC data - this gets cached."""
    try:
        gsc_client = GSCClient()
        gsc_client.authenticate()
        
        # Get search analytics data
        df = gsc_client.get_search_analytics_data(
            start_date=start_date_str,
            end_date=end_date_str
        )
        
        return df
        
    except Exception as e:
        st.error(f"Error fetching GSC data: {str(e)}")
        return None

def fetch_aeo_geo_data():
    """Fetch and analyze GSC data for AEO/GEO optimization."""
    try:
        with st.spinner("🔍 Fetching Google Search Console data..."):
            # Calculate dates
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=90)
            
            # Get cached raw data
            df = fetch_raw_gsc_data(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            if df is None or df.empty:
                return None
            
            # Filter for non-brand keywords
            brand_keywords = config.BRAND_KEYWORDS
            brand_pattern = '|'.join([re.escape(brand.lower()) for brand in brand_keywords])
            df_filtered = df[~df['query'].str.lower().str.contains(brand_pattern, na=False)].copy()
            
            # Filter out permanently deleted keywords
            deleted_keywords = load_deleted_keywords()
            if deleted_keywords:
                df_filtered = df_filtered[~df_filtered['query'].isin(deleted_keywords)].copy()
            
            # Add AEO/GEO analysis columns using assign to avoid pandas warnings
            from ahrefs_data_loader import has_ahrefs_data, get_real_search_volume
            
            df_filtered = df_filtered.assign(
                Intent_Type=df_filtered['query'].apply(classify_aeo_geo_intent),
                SERP_Features=df_filtered['query'].apply(analyze_serp_features),
                Is_Question=df_filtered['query'].str.lower().str.contains('how|what|why|when|where|who', na=False),
                Answer_Potential=df_filtered.apply(calculate_answer_potential, axis=1),
                Est_Search_Volume=df_filtered.apply(lambda row: get_real_search_volume(row['query'], row['impressions']), axis=1),
                Data_Source=df_filtered['query'].apply(lambda keyword: 'Ahrefs' if has_ahrefs_data(keyword) else 'GSC Est.')
            )
            
            return df_filtered
        
    except Exception as e:
        st.error(f"Error fetching AEO/GEO data: {str(e)}")
        return None

def create_summary_metrics(df):
    """Create summary metrics for AEO/GEO analysis."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_queries = len(df)
        st.metric(
            label="Total Queries",
            value=f"{total_queries:,}",
            help="Total non-brand queries analyzed"
        )
    
    with col2:
        question_queries = len(df[df['Is_Question'] == True])
        question_pct = (question_queries / total_queries * 100) if total_queries > 0 else 0
        st.metric(
            label="Question-Based",
            value=f"{question_queries:,}",
            delta=f"{question_pct:.1f}% of total",
            help="Queries starting with how/what/why/when/where/who"
        )
    
    with col3:
        high_potential = len(df[df['Answer_Potential'] >= 70])
        high_pct = (high_potential / total_queries * 100) if total_queries > 0 else 0
        st.metric(
            label="High Answer Potential",
            value=f"{high_potential:,}",
            delta=f"{high_pct:.1f}% of total",
            help="Queries with Answer Potential score ≥ 70"
        )
    
    with col4:
        avg_position = df['position'].mean()
        st.metric(
            label="Avg Position",
            value=f"{avg_position:.1f}",
            help="Average ranking position across all queries"
        )

def create_visualizations(df):
    """Create visualizations for AEO/GEO analysis."""
    col1, col2 = st.columns(2)
    
    with col1:
        # Intent type breakdown
        intent_counts = df['Intent_Type'].value_counts()
        fig_pie = px.pie(
            values=intent_counts.values,
            names=intent_counts.index,
            title="Query Intent Distribution",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Answer potential distribution
        df['Potential_Tier'] = pd.cut(
            df['Answer_Potential'], 
            bins=[0, 40, 70, 100], 
            labels=['Low (0-40)', 'Medium (40-70)', 'High (70-100)']
        )
        tier_counts = df['Potential_Tier'].value_counts()
        
        fig_bar = px.bar(
            x=tier_counts.values,
            y=tier_counts.index,
            orientation='h',
            title="Answer Potential Distribution",
            color=tier_counts.values,
            color_continuous_scale=['#ff6b6b', '#ffd93d', '#6bcf7f']
        )
        fig_bar.update_layout(
            yaxis={'categoryorder':'total ascending'},
            showlegend=False
        )
        st.plotly_chart(fig_bar, use_container_width=True)

def display_analysis_table(df):
    """Display interactive analysis table with filtering."""
    st.subheader("🔍 AEO/GEO Query Analysis")
    
    # Load permanently deleted keywords
    deleted_keywords = load_deleted_keywords()
    
    # Remove deleted keywords from the dataframe (this is additional safety since they should already be filtered)
    if deleted_keywords:
        df = df[~df['query'].isin(deleted_keywords)].copy()
    
    # Filters
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        intent_filter = st.selectbox(
            "Filter by Intent Type",
            ['All'] + list(df['Intent_Type'].unique())
        )
    
    with col2:
        question_filter = st.selectbox(
            "Question-Based Queries",
            ['All', 'Questions Only', 'Non-Questions Only']
        )
    
    with col3:
        # Get all unique SERP features
        all_features = set()
        for features_list in df['SERP_Features']:
            all_features.update(features_list)
        
        serp_features_filter = st.multiselect(
            "Filter by SERP Features",
            options=sorted(list(all_features)),
            default=[],
            help="Select one or more SERP features to filter by"
        )
    
    with col4:
        min_potential = st.slider(
            "Min Answer Potential",
            min_value=0,
            max_value=100,
            value=50,
            step=5
        )
    
    with col5:
        min_impressions = st.number_input(
            "Min Impressions",
            min_value=0,
            max_value=int(df['impressions'].max()),
            value=10,
            step=10,
            help="Filter out keywords below this impression threshold"
        )
    
    # Apply filters
    filtered_df = df.copy()
    
    if intent_filter != 'All':
        filtered_df = filtered_df[filtered_df['Intent_Type'] == intent_filter]
    
    if question_filter == 'Questions Only':
        filtered_df = filtered_df[filtered_df['Is_Question'] == True]
    elif question_filter == 'Non-Questions Only':
        filtered_df = filtered_df[filtered_df['Is_Question'] == False]
    
    # Apply SERP features filter
    if serp_features_filter:
        def has_selected_features(features_list):
            return any(feature in features_list for feature in serp_features_filter)
        filtered_df = filtered_df[filtered_df['SERP_Features'].apply(has_selected_features)]
    
    # Apply minimum thresholds
    filtered_df = filtered_df[filtered_df['Answer_Potential'] >= min_potential]
    filtered_df = filtered_df[filtered_df['impressions'] >= min_impressions]
    
    # Sort by answer potential
    filtered_df = filtered_df.sort_values('Answer_Potential', ascending=False)
    
    # Display results count and delete controls
    results_col, delete_col = st.columns([3, 1])
    
    with results_col:
        total_deleted = len(deleted_keywords) if deleted_keywords else 0
        st.info(f"📊 Showing {len(filtered_df):,} queries (filtered from {len(df):,} total) | 🗑️ {total_deleted} permanently deleted")
    
    with delete_col:
        if st.button("🗑️ Delete Selected", help="Permanently delete selected queries from analysis"):
            # Get selected queries from the edited data
            if 'aeo_edited_data' in st.session_state and st.session_state.aeo_edited_data is not None:
                # Find checked rows
                selected_queries = []
                for idx, row in st.session_state.aeo_edited_data.iterrows():
                    if row.get('Delete', False):  # Check if the checkbox is checked
                        selected_queries.append(row['Query'])
                
                if selected_queries:
                    # Add selected queries to permanently deleted set
                    deleted_keywords.update(selected_queries)
                    save_deleted_keywords(deleted_keywords)
                    st.success(f"Permanently deleted {len(selected_queries)} queries from analysis!")
                    # Force refresh of the page
                    st.rerun()
                else:
                    st.warning("No queries selected for deletion")
            else:
                st.warning("No queries selected for deletion")
    
    if deleted_keywords:
        if st.button("🔄 Reset All Deleted Queries", help="Restore all permanently deleted queries"):
            # Clear the deleted keywords file
            save_deleted_keywords(set())
            st.success("All permanently deleted queries restored!")
            st.rerun()
    
    # Display table
    display_columns = [
        'query', 'position', 'impressions', 'clicks', 'ctr', 'Est_Search_Volume', 'Data_Source',
        'Intent_Type', 'Is_Question', 'Answer_Potential', 'SERP_Features'
    ]
    
    display_df = filtered_df[display_columns].copy()
    
    # Add checkbox column for deletion
    display_df.insert(0, 'Delete', False)
    
    # Convert CTR from decimal to percentage for display (GSC gives CTR as decimal like 0.085)
    display_df['ctr'] = display_df['ctr'] * 100
    
    # Format numeric columns for display (keep as numeric for sorting)
    display_df['Answer_Potential'] = display_df['Answer_Potential'].round(0).astype(int)
    
    # Rename columns for display
    display_df.columns = [
        'Delete', 'Query', 'Position', 'Impressions', 'Clicks', 'CTR', 'Est. Search Volume', 'Data Source',
        'Intent Type', 'Question?', 'Answer Potential', 'SERP Features'
    ]
    
    # Column configuration for the data editor
    column_config = {
        "Delete": st.column_config.CheckboxColumn(
            "Select",
            help="Check to select query for deletion",
            default=False,
            width="small"
        ),
        "Query": st.column_config.TextColumn(
            "Query",
            width="large"
        ),
        "Position": st.column_config.NumberColumn(
            "Position",
            format="%.1f",
            width="small"
        ),
        "Impressions": st.column_config.NumberColumn(
            "Impressions",
            format="%d",
            width="small"
        ),
        "Clicks": st.column_config.NumberColumn(
            "Clicks", 
            format="%d",
            width="small"
        ),
        "CTR": st.column_config.NumberColumn(
            "CTR",
            format="%.1f%%",
            width="small"
        ),
        "Est. Search Volume": st.column_config.NumberColumn(
            "Est. Volume",
            help="Monthly search volume (Ahrefs when available, estimated otherwise)",
            format="%d",
            width="small"
        ),
        "Data Source": st.column_config.TextColumn(
            "Source",
            help="Data source: Ahrefs (real data) or GSC Est. (estimated)",
            width="small"
        ),
        "Intent Type": st.column_config.TextColumn(
            "Intent",
            width="medium"
        ),
        "Question?": st.column_config.CheckboxColumn(
            "Q?",
            width="small"
        ),
        "Answer Potential": st.column_config.NumberColumn(
            "Answer Potential",
            format="%d",
            width="small"
        ),
        "SERP Features": st.column_config.TextColumn(
            "SERP Features",
            width="medium"
        )
    }
    
    # Display the interactive data editor
    edited_df = st.data_editor(
        display_df,
        use_container_width=True,
        height=600,
        column_config=column_config,
        disabled=list(display_df.columns[1:]),  # Disable editing of all columns except Delete
        hide_index=True,
        key="aeo_data_editor"
    )
    
    # Store edited data in session state for deletion processing
    st.session_state.aeo_edited_data = edited_df
    
    # Show selected count
    if edited_df is not None:
        selected_count = edited_df['Delete'].sum()
        if selected_count > 0:
            st.info(f"🗑️ {selected_count} queries selected for deletion")
    
    return filtered_df

def display_insights(filtered_df):
    """Display key insights and recommendations."""
    st.markdown("---")
    st.subheader("🚀 Key Insights & Recommendations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🎯 Top Question-Based Opportunities:**")
        question_ops = filtered_df[filtered_df['Is_Question'] == True].nlargest(5, 'Answer_Potential')
        
        if len(question_ops) > 0:
            for idx, row in question_ops.iterrows():
                st.write(f"• **{row['query']}** (Potential: {row['Answer_Potential']:.0f}, Pos: {row['position']:.1f})")
        else:
            st.write("No question-based queries in current filter")
    
    with col2:
        st.markdown("**📈 High-Volume Answer Targets:**")
        high_volume = filtered_df.nlargest(5, 'impressions')
        
        if len(high_volume) > 0:
            for idx, row in high_volume.iterrows():
                st.write(f"• **{row['query']}** ({row['impressions']:,} impressions, {row['Intent_Type']})")
        else:
            st.write("No queries in current filter")

def display_glossary():
    """Display AEO/GEO glossary and definitions."""
    st.markdown("---")
    st.header("📖 AEO/GEO Glossary")
    
    # Intent Types & Strategies
    st.subheader("🎯 Intent Types & Optimization Strategies")
    
    intent_col1, intent_col2 = st.columns(2)
    
    with intent_col1:
        st.markdown("""
        **🔍 Question-Based**
        - **What it is**: Queries starting with how, what, why, when, where, who
        - **Strategy**: Target featured snippets with 40-60 word direct answers
        - **Format**: Start with the question as H2, provide concise answer immediately
        - **Example**: "How to teach elementary math?" → Direct answer in first paragraph
        
        **📚 Definition**
        - **What it is**: Queries seeking explanations or meanings
        - **Strategy**: Create knowledge panel-optimized content
        - **Format**: Term + definition + detailed explanation + examples
        - **Example**: "What is synthesis tutoring?" → Clear definition + benefits
        
        **⚖️ Comparison**
        - **What it is**: Queries comparing options (vs, versus, compare)
        - **Strategy**: Build comprehensive comparison tables
        - **Format**: Comparison table + pros/cons + recommendation
        - **Example**: "Online vs in-person tutoring" → Side-by-side comparison
        """)
    
    with intent_col2:
        st.markdown("""
        **🛠️ How-To**
        - **What it is**: Instructional queries requiring step-by-step guidance
        - **Strategy**: Create tutorial content with numbered steps
        - **Format**: Numbered list + images/videos + clear instructions
        - **Example**: "How to solve algebra problems" → Step-by-step guide
        
        **📝 List-Based**
        - **What it is**: Queries seeking lists or examples
        - **Strategy**: Create structured list content with descriptions
        - **Format**: Numbered/bulleted lists + brief explanations
        - **Example**: "Best math apps for kids" → Numbered list with details
        
        **💡 Factual**
        - **What it is**: Direct factual queries requiring concise answers
        - **Strategy**: Provide immediate, authoritative answers
        - **Format**: Direct answer + supporting context + sources
        - **Example**: "When should kids start algebra?" → Age + reasoning
        """)
    
    # Technical Definitions
    st.subheader("📊 Technical Definitions")
    
    tech_col1, tech_col2 = st.columns(2)
    
    with tech_col1:
        st.markdown("""
        **Position**
        - **Definition**: Your website's average ranking in Google search results (1 = top result)
        - **SERP Context**: Position 1-3 appear "above the fold", positions 4-10 require scrolling
        - **Featured Snippet**: Can appear at "position 0" above all organic results
        - **AEO Impact**: Higher positions (1-10) have better foundation for answer optimization
        
        **Est. Search Volume**
        - **Definition**: Estimated total monthly searches for the keyword across all websites
        - **Calculation**: Based on your impressions and estimated market share
        - **Note**: This is an approximation, not exact volume data
        """)
    
    with tech_col2:
        st.markdown("""
        **Answer Potential Score**
        - **Position Factor (40%)**: Higher rankings = better optimization foundation
        - **Volume Factor (30%)**: More searches = bigger opportunity
        - **Question Format (20%)**: Question-based queries score higher
        - **Query Length (10%)**: Longer queries often better for detailed answers
        
        **SERP Features**
        - **Featured Snippet**: Answer box at position 0
        - **Knowledge Panel**: Information box on the right side
        - **FAQ**: Expandable question/answer sections
        - **How-To**: Step-by-step rich snippets
        """)
    
    # Strategy Summary
    st.subheader("🚀 Overall AEO vs GEO Strategy")
    
    strategy_col1, strategy_col2 = st.columns(2)
    
    with strategy_col1:
        st.markdown("""
        **AEO (Answer Engine Optimization)**
        - Target traditional search engine features
        - Focus on featured snippets and knowledge panels
        - Use structured data markup
        - Create concise, direct answers (40-60 words)
        - Optimize for voice search queries
        """)
    
    with strategy_col2:
        st.markdown("""
        **GEO (Generative Engine Optimization)**
        - Optimize for AI chatbots and generative search
        - Create comprehensive, contextual content
        - Focus on E-A-T (Expertise, Authority, Trust) signals
        - Use natural language and conversational tone
        - Build authoritative, citable content sources
        """)

def add_navigation():
    """Add smart navigation that works both locally and in cloud deployment."""
    import os
    
    # Detect environment
    is_cloud = os.getenv('STREAMLIT_CLOUD', False) or 'streamlit.app' in os.getenv('STREAMLIT_SERVER_ADDRESS', '')
    
    st.sidebar.markdown("## 🧭 Dashboard Navigation")
    st.sidebar.markdown("**Current:** 🤖 AEO/GEO Analysis")
    
    if is_cloud:
        # For cloud deployment, provide instructions
        st.sidebar.markdown("### 🎯 SEO Dashboard")
        st.sidebar.info("Deploy the `dashboard.py` as a separate Streamlit app for SEO keyword analysis")
    else:
        # For local development, provide working links
        st.sidebar.markdown("""
        <a href="http://localhost:8504" target="_blank" style="
            display: inline-block;
            padding: 0.5rem 1rem;
            background-color: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 0.3rem;
            font-weight: bold;
            margin: 0.5rem 0;
            text-align: center;
            width: 200px;
        ">🎯 Open SEO Dashboard</a>
        """, unsafe_allow_html=True)
        st.sidebar.caption("💡 Run: `streamlit run dashboard.py --server.port 8504`")
    
    st.sidebar.markdown("---")

def main():
    """Main dashboard function."""
    # Navigation
    add_navigation()
    
    # Header
    st.title("🤖 AEO/GEO Analysis Dashboard")
    st.markdown("### Answer Engine & Generative Engine Optimization for synthesis.com/tutor")
    
    # Initialize session state for data caching
    if 'aeo_data_loaded' not in st.session_state:
        st.session_state.aeo_data_loaded = False
        st.session_state.aeo_data = None
    
    # Load data only once or when explicitly refreshed
    if not st.session_state.aeo_data_loaded or st.session_state.aeo_data is None:
        df = fetch_aeo_geo_data()
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