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

# Page configuration
st.set_page_config(
    page_title="AEO/GEO Analysis Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

def estimate_search_volume(impressions):
    """Estimate total search volume based on impressions (same method as SEO dashboard)."""
    # Assumes your impressions represent ~10% of total search volume
    return int((impressions / 0.1))

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

@st.cache_data
def fetch_aeo_geo_data():
    """Fetch and analyze GSC data for AEO/GEO optimization."""
    try:
        with st.spinner("🔍 Fetching Google Search Console data..."):
            gsc_client = GSCClient()
            gsc_client.authenticate()
            
            # Fetch data from last 90 days
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=90)
            
            # Get search analytics data
            df = gsc_client.get_search_analytics_data(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            if df is None or df.empty:
                return None
            
            # Filter for non-brand keywords
            brand_keywords = config.BRAND_KEYWORDS
            brand_pattern = '|'.join([re.escape(brand.lower()) for brand in brand_keywords])
            df_filtered = df[~df['query'].str.lower().str.contains(brand_pattern, na=False)]
            
            # Add AEO/GEO analysis columns
            df_filtered = df_filtered.copy()  # Fix pandas warning
            df_filtered['Intent_Type'] = df_filtered['query'].apply(classify_aeo_geo_intent)
            df_filtered['SERP_Features'] = df_filtered['query'].apply(analyze_serp_features)
            df_filtered['Is_Question'] = df_filtered['query'].str.lower().str.contains('how|what|why|when|where|who', na=False)
            df_filtered['Answer_Potential'] = df_filtered.apply(calculate_answer_potential, axis=1)
            df_filtered['Est_Search_Volume'] = df_filtered['impressions'].apply(lambda x: estimate_search_volume(x))
            
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
    
    # Display results count
    st.info(f"📊 Showing {len(filtered_df):,} queries (filtered from {len(df):,} total)")
    
    # Display table
    display_columns = [
        'query', 'position', 'impressions', 'clicks', 'ctr', 'Est_Search_Volume',
        'Intent_Type', 'Is_Question', 'Answer_Potential', 'SERP_Features'
    ]
    
    display_df = filtered_df[display_columns].copy()
    display_df['ctr'] = display_df['ctr'].apply(lambda x: f"{x:.1%}")
    display_df['position'] = display_df['position'].apply(lambda x: f"{x:.1f}")
    display_df['Answer_Potential'] = display_df['Answer_Potential'].apply(lambda x: f"{x:.0f}")
    display_df['Est_Search_Volume'] = display_df['Est_Search_Volume'].apply(lambda x: f"{x:,}")
    
    # Rename columns for display
    display_df.columns = [
        'Query', 'Position', 'Impressions', 'Clicks', 'CTR', 'Est. Search Volume',
        'Intent Type', 'Question?', 'Answer Potential', 'SERP Features'
    ]
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
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

def main():
    """Main dashboard function."""
    # Header
    st.title("🤖 AEO/GEO Analysis Dashboard")
    st.markdown("### Answer Engine & Generative Engine Optimization for synthesis.com/tutor")
    
    # Load data
    df = fetch_aeo_geo_data()
    
    if df is None or len(df) == 0:
        st.error("Unable to fetch data from Google Search Console. Please check your connection and authentication.")
        return
    
    st.success(f"✅ Loaded {len(df):,} non-brand queries for AEO/GEO analysis")
    
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