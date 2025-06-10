#!/usr/bin/env python3
"""
Keyword Opportunities Dashboard

Interactive Streamlit dashboard for viewing and analyzing keyword opportunities
from Google Search Console data with sorting, filtering, and pagination.
"""

import streamlit as st
import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import re

# Page configuration
st.set_page_config(
    page_title="SEO Keyword Opportunities Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark mode table and improved styling
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
    

</style>
""", unsafe_allow_html=True)

def estimate_keyword_difficulty(keyword):
    """Estimate keyword difficulty based on keyword characteristics."""
    keyword_lower = keyword.lower()
    base_difficulty = 30
    
    # Length factor (longer = easier)
    if len(keyword) > 30:
        base_difficulty -= 15
    elif len(keyword) > 20:
        base_difficulty -= 10
    elif len(keyword) < 10:
        base_difficulty += 15
    
    # Competitive terms
    if any(term in keyword_lower for term in ['ai', 'best', 'top', 'free']):
        base_difficulty += 20
    
    # Educational terms (moderate competition)
    if any(term in keyword_lower for term in ['tutor', 'learn', 'education', 'math']):
        base_difficulty += 10
    
    # Long-tail questions (easier)
    if any(starter in keyword_lower for starter in ['how to', 'what is', 'why does', 'when should']):
        base_difficulty -= 15
    
    # Brand misspellings (easier)
    if any(brand in keyword_lower for brand in ['synthesis', 'synthesi', 'sythesis']):
        base_difficulty -= 20
    
    return max(5, min(95, base_difficulty + np.random.randint(-10, 11)))

def estimate_cpc(keyword):
    """Estimate CPC based on keyword characteristics."""
    keyword_lower = keyword.lower()
    base_cpc = 1.50
    
    # Educational/tutoring terms have higher CPC
    if any(term in keyword_lower for term in ['tutor', 'tutoring', 'education', 'learn']):
        base_cpc *= 2.5
    
    # AI terms are competitive
    if 'ai' in keyword_lower:
        base_cpc *= 2.0
    
    # Commercial intent terms
    if any(term in keyword_lower for term in ['best', 'top', 'review', 'compare']):
        base_cpc *= 1.8
    
    # Specific/long-tail terms have lower CPC
    if len(keyword) > 25:
        base_cpc *= 0.6
    
    # Add some randomness
    base_cpc *= (0.7 + np.random.random() * 0.6)
    
    return round(base_cpc, 2)

def classify_search_intent(keyword):
    """Classify search intent based on keyword patterns."""
    keyword_lower = keyword.lower()
    
    # Navigational intent
    if any(brand in keyword_lower for brand in ['synthesis', 'synthesi', 'sythesis']):
        return 'Navigational'
    
    # Transactional intent
    if any(term in keyword_lower for term in ['buy', 'price', 'cost', 'hire', 'sign up', 'subscribe']):
        return 'Transactional'
    
    # Commercial intent
    if any(term in keyword_lower for term in ['best', 'top', 'review', 'compare', 'vs', 'alternative']):
        return 'Commercial'
    
    # Informational intent (questions, how-to, etc.)
    if any(starter in keyword_lower for starter in ['how', 'what', 'why', 'when', 'where', 'who']):
        return 'Informational'
    
    # Educational content (mostly informational)
    if any(term in keyword_lower for term in ['learn', 'education', 'study', 'guide', 'tutorial']):
        return 'Informational'
    
    # Default to informational for educational content
    return 'Informational'

@st.cache_data
def load_latest_data():
    """Load the most recent keyword opportunities CSV file and enhance with additional data."""
    # Find the most recent CSV file
    csv_files = glob.glob("keyword_opportunities_*.csv")
    if not csv_files:
        return None, None
    
    latest_file = max(csv_files, key=os.path.getctime)
    df = pd.read_csv(latest_file)
    
    # Convert percentage strings to float
    df['Current CTR'] = df['Current CTR'].str.rstrip('%').astype(float) / 100
    df['CTR Potential'] = df['CTR Potential'].str.rstrip('%').astype(float) / 100
    
    # Add new columns if they don't exist
    if 'Keyword Difficulty' not in df.columns:
        df['Keyword Difficulty'] = df['Keyword'].apply(estimate_keyword_difficulty)
    
    if 'Average CPC' not in df.columns:
        df['Average CPC'] = df['Keyword'].apply(estimate_cpc)
    
    if 'Search Intent' not in df.columns:
        df['Search Intent'] = df['Keyword'].apply(classify_search_intent)
    
    # Add real search volume from Ahrefs with fallback to estimates
    if 'Est. Monthly Volume' not in df.columns:
        from ahrefs_data_loader import get_real_search_volume, has_ahrefs_data
        
        df['Est. Monthly Volume'] = df.apply(
            lambda row: get_real_search_volume(row['Keyword'], row['Monthly Impressions']), 
            axis=1
        )
        
        # Add data source indicator
        df['Data Source'] = df['Keyword'].apply(
            lambda keyword: 'Ahrefs' if has_ahrefs_data(keyword) else 'GSC Est.'
        )
    
    return df, latest_file

def save_updated_data(df, filename):
    """Save the updated dataframe back to CSV."""
    # Convert CTR columns back to percentage strings for consistency
    df_save = df.copy()
    df_save['Current CTR'] = df_save['Current CTR'].apply(lambda x: f"{x:.2%}")
    df_save['CTR Potential'] = df_save['CTR Potential'].apply(lambda x: f"{x:.2%}")
    
    # Remove the estimated volume column from save (it's calculated)
    if 'Est. Monthly Volume' in df_save.columns:
        df_save = df_save.drop('Est. Monthly Volume', axis=1)
    
    df_save.to_csv(filename, index=False)
    st.cache_data.clear()  # Clear cache to reload data

def format_large_number(num):
    """Format large numbers with commas."""
    return f"{num:,}"

def create_summary_metrics(df):
    """Create summary metrics cards."""
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

def create_visualizations(df):
    """Create dashboard visualizations."""
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
        # Customizable breakdown chart
        breakdown_options = {
            'Search Intent': 'Search Intent',
            'Opportunity Type': 'Opportunity Type', 
            'Priority': 'Priority',
            'Keyword Difficulty Range': 'Keyword Difficulty'
        }
        
        selected_breakdown = st.selectbox(
            "Chart Breakdown:",
            options=list(breakdown_options.keys()),
            index=0,
            key="breakdown_select"
        )
        
        breakdown_column = breakdown_options[selected_breakdown]
        
        if breakdown_column == 'Keyword Difficulty':
            # Create difficulty ranges for better visualization
            df_viz = df.copy()
            df_viz['Difficulty Range'] = pd.cut(
                df_viz['Keyword Difficulty'], 
                bins=[0, 20, 40, 60, 80, 100], 
                labels=['Very Easy (0-20)', 'Easy (21-40)', 'Medium (41-60)', 'Hard (61-80)', 'Very Hard (81-100)']
            )
            breakdown_counts = df_viz['Difficulty Range'].value_counts()
        else:
            breakdown_counts = df[breakdown_column].value_counts()
        
        fig_bar = px.bar(
            x=breakdown_counts.values,
            y=breakdown_counts.index,
            orientation='h',
            title=f"Keywords by {selected_breakdown}",
            labels={'x': 'Number of Keywords', 'y': selected_breakdown},
            color=breakdown_counts.values,
            color_continuous_scale='viridis'
        )
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)

def filter_dataframe(df):
    """Add filters to the sidebar."""
    st.sidebar.header("🔍 Filters")
    
    # Priority filter
    priorities = ['All'] + list(df['Priority'].unique())
    selected_priority = st.sidebar.selectbox("Priority Level", priorities)
    
    # Opportunity type filter
    opp_types = ['All'] + list(df['Opportunity Type'].unique())
    selected_opp_type = st.sidebar.selectbox("Opportunity Type", opp_types)
    
    # Search intent filter
    intents = ['All'] + list(df['Search Intent'].unique())
    selected_intent = st.sidebar.selectbox("Search Intent", intents)
    
    # Position range filter
    min_pos, max_pos = st.sidebar.slider(
        "Position Range",
        min_value=float(df['Current Position'].min()),
        max_value=float(df['Current Position'].max()),
        value=(float(df['Current Position'].min()), float(df['Current Position'].max())),
        step=0.1
    )
    
    # Opportunity score filter
    min_score, max_score = st.sidebar.slider(
        "Opportunity Score Range",
        min_value=float(df['Opportunity Score'].min()),
        max_value=float(df['Opportunity Score'].max()),
        value=(float(df['Opportunity Score'].min()), float(df['Opportunity Score'].max())),
        step=0.1,
        key="opp_score_slider"
    )
    
    # Keyword difficulty filter
    min_diff, max_diff = st.sidebar.slider(
        "Keyword Difficulty Range",
        min_value=int(df['Keyword Difficulty'].min()),
        max_value=int(df['Keyword Difficulty'].max()),
        value=(int(df['Keyword Difficulty'].min()), int(df['Keyword Difficulty'].max())),
        step=1
    )
    
    # Monthly search volume filter
    min_volume = st.sidebar.number_input(
        "Minimum Monthly Search Volume",
        min_value=0,
        max_value=int(df['Est. Monthly Volume'].max()),
        value=0,
        step=100
    )
    
    # Keyword search
    keyword_search = st.sidebar.text_input("Search Keywords", placeholder="Enter keyword to search...")
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_priority != 'All':
        filtered_df = filtered_df[filtered_df['Priority'] == selected_priority]
    
    if selected_opp_type != 'All':
        filtered_df = filtered_df[filtered_df['Opportunity Type'] == selected_opp_type]
    
    if selected_intent != 'All':
        filtered_df = filtered_df[filtered_df['Search Intent'] == selected_intent]
    
    filtered_df = filtered_df[
        (filtered_df['Current Position'] >= min_pos) & 
        (filtered_df['Current Position'] <= max_pos)
    ]
    
    filtered_df = filtered_df[
        (filtered_df['Opportunity Score'] >= min_score) & 
        (filtered_df['Opportunity Score'] <= max_score)
    ]
    
    filtered_df = filtered_df[
        (filtered_df['Keyword Difficulty'] >= min_diff) & 
        (filtered_df['Keyword Difficulty'] <= max_diff)
    ]
    
    filtered_df = filtered_df[filtered_df['Est. Monthly Volume'] >= min_volume]
    
    if keyword_search:
        filtered_df = filtered_df[
            filtered_df['Keyword'].str.contains(keyword_search, case=False, na=False)
        ]
    
    return filtered_df

def display_paginated_table(df, filename):
    """Display the dataframe with pagination, sorting, and deletion functionality."""
    st.subheader("📊 Keyword Opportunities")
    
    # Add pagination and delete controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("*Click column headers to sort ascending/descending*")
    
    with col2:
        rows_per_page = st.selectbox("Rows per page", [25, 50, 100, 200], index=1)
    
    with col3:
        if st.button("🗑️ Delete Selected", help="Delete selected keywords from database"):
            # Get selected keywords from the edited data
            if 'edited_data' in st.session_state and st.session_state.edited_data is not None:
                # Find checked rows
                selected_keywords = []
                for idx, row in st.session_state.edited_data.iterrows():
                    if row.get('Delete', False):  # Check if the checkbox is checked
                        selected_keywords.append(row['Keyword'])
                
                if selected_keywords:
                    # Remove selected keywords from the dataframe
                    original_df, _ = load_latest_data()
                    updated_df = original_df[~original_df['Keyword'].isin(selected_keywords)]
                    save_updated_data(updated_df, filename)
                    st.success(f"Deleted {len(selected_keywords)} keywords!")
                    # Clear the edited data to reset checkboxes
                    if 'edited_data' in st.session_state:
                        del st.session_state.edited_data
                    # Force refresh of the page to update insights
                    st.rerun()
                else:
                    st.warning("No keywords selected for deletion")
            else:
                st.warning("No keywords selected for deletion")
    
    # Use the original dataframe without pre-sorting to enable column header sorting
    df_sorted = df
    
    # Calculate pagination
    total_rows = len(df_sorted)
    total_pages = (total_rows - 1) // rows_per_page + 1
    
    # Page selector
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        current_page = st.number_input(
            f"Page (1-{total_pages})",
            min_value=1,
            max_value=total_pages,
            value=1,
            step=1
        )
    
    # Calculate start and end indices
    start_idx = (current_page - 1) * rows_per_page
    end_idx = min(start_idx + rows_per_page, total_rows)
    
    # Display current page data
    page_df = df_sorted.iloc[start_idx:end_idx].copy()
    
    # Prepare the display dataframe for proper sorting
    display_df = page_df.copy()
    
    # Convert CTR values from decimals to percentages for display
    display_df['Current CTR'] = display_df['Current CTR'] * 100
    display_df['CTR Potential'] = display_df['CTR Potential'] * 100
    
    # Add interactive checkbox column for deletion
    display_df.insert(0, 'Delete', False)  # Add boolean column for checkboxes
    
    # Keep numeric columns as numbers for proper sorting, format display in column config
    # Only format text columns that won't be sorted numerically
    
    # Reorder columns for better UX
    column_order = [
        'Delete', 'Keyword', 'Current Position', 'Opportunity Score', 'Priority', 'Opportunity Type',
        'Monthly Impressions', 'Monthly Clicks', 'Current CTR', 'CTR Potential', 'Traffic Potential',
        'Est. Monthly Volume', 'Data Source', 'Keyword Difficulty', 'Average CPC', 'Search Intent'
    ]
    display_df = display_df[column_order]
    
    # Create column configuration for the data editor with proper formatting
    column_config = {
        "Delete": st.column_config.CheckboxColumn(
            "Select",
            help="Check to select keyword for deletion",
            default=False,
            width="small"
        ),
        "Keyword": st.column_config.TextColumn(
            "Keyword",
            help="The search keyword",
            width="medium"
        ),
        "Current Position": st.column_config.NumberColumn(
            "Position",
            help="Current ranking position",
            format="%.1f",
            width="small"
        ),
        "Opportunity Score": st.column_config.NumberColumn(
            "Score",
            help="Opportunity score (0-100)",
            format="%.1f",
            width="small"
        ),
        "Priority": st.column_config.TextColumn(
            "Priority",
            width="small"
        ),
        "Opportunity Type": st.column_config.TextColumn(
            "Type",
            width="medium"
        ),
        "Monthly Impressions": st.column_config.NumberColumn(
            "Impressions",
            help="Monthly impressions from GSC",
            format="%d",
            width="small"
        ),
        "Monthly Clicks": st.column_config.NumberColumn(
            "Clicks",
            help="Monthly clicks from GSC",
            format="%d",
            width="small"
        ),
        "Current CTR": st.column_config.NumberColumn(
            "CTR",
            help="Current click-through rate",
            format="%.1f%%",
            width="small"
        ),
        "CTR Potential": st.column_config.NumberColumn(
            "CTR Pot.",
            help="CTR improvement potential", 
            format="%.1f%%",
            width="small"
        ),
        "Traffic Potential": st.column_config.NumberColumn(
            "Traffic Pot.",
            help="Additional monthly clicks potential",
            format="%d",
            width="small"
        ),
        "Est. Monthly Volume": st.column_config.NumberColumn(
            "Volume",
            help="Monthly search volume (Ahrefs when available, estimated otherwise)",
            format="%d",
            width="small"
        ),
        "Data Source": st.column_config.TextColumn(
            "Source",
            help="Data source: Ahrefs (real data) or GSC Est. (estimated)",
            width="small"
        ),
        "Keyword Difficulty": st.column_config.NumberColumn(
            "KD",
            help="Keyword Difficulty (0-100)",
            format="%d",
            width="small"
        ),
        "Average CPC": st.column_config.NumberColumn(
            "CPC",
            help="Estimated cost per click",
            format="$%.2f",
            width="small"
        ),
        "Search Intent": st.column_config.TextColumn(
            "Intent",
            help="Classified search intent",
            width="small"
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
        key=f"data_editor_page_{current_page}"
    )
    
    # Store edited data in session state for deletion processing
    st.session_state.edited_data = edited_df
    
    # Show pagination info
    st.caption(f"Showing rows {start_idx + 1}-{end_idx} of {total_rows} total keywords")
    
    # Show selected count
    if edited_df is not None:
        selected_count = edited_df['Delete'].sum()
        if selected_count > 0:
            st.info(f"🗑️ {selected_count} keywords selected for deletion")
    

    
    return page_df

def export_filtered_data(df):
    """Allow users to export filtered data."""
    if st.sidebar.button("📥 Export Filtered Data"):
        # Prepare export dataframe
        export_df = df.copy()
        export_df['Current CTR'] = export_df['Current CTR'].apply(lambda x: f"{x:.2%}")
        export_df['CTR Potential'] = export_df['CTR Potential'].apply(lambda x: f"{x:.2%}")
        
        csv = export_df.to_csv(index=False)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"filtered_opportunities_{timestamp}.csv"
        
        st.sidebar.download_button(
            label="Download CSV",
            data=csv,
            file_name=filename,
            mime="text/csv"
        )

def main():
    """Main dashboard function."""
    # Navigation
    st.sidebar.markdown("## 🧭 Navigation")
    st.sidebar.markdown("**Current:** 🎯 SEO Dashboard")
    st.sidebar.markdown("""
    <a href="http://localhost:8505" target="_blank" style="
        display: inline-block;
        padding: 0.5rem 1rem;
        background-color: #FF6B6B;
        color: white;
        text-decoration: none;
        border-radius: 0.3rem;
        font-weight: bold;
        margin: 0.5rem 0;
    ">🤖 Open AEO/GEO Dashboard</a>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    
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

def display_glossary():
    """Display comprehensive glossary of all terms used in the dashboard."""
    st.markdown("---")
    st.header("📖 Glossary & Definitions")
    
    # Column Headers
    st.subheader("Column Headers")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Keyword**: The search query that users type into Google to find content.
        
        **Current Position**: Your website's average ranking position for this keyword in Google search results (1 = top position).
        
        **Opportunity Score**: A comprehensive score (0-100) that ranks keywords by their improvement potential:
        - **90+**: Immediate action recommended
        - **70-89**: High priority opportunities  
        - **40-69**: Medium priority opportunities
        - **<40**: Low priority, long-term targets
        
        **Priority**: Simplified categorization based on Opportunity Score (High/Medium/Low).
        
        **Monthly Impressions**: How many times your website appeared in Google search results for this keyword over the past month (from Google Search Console).
        
        **Monthly Clicks**: How many times users actually clicked on your website from search results for this keyword over the past month.
        
        **Current CTR**: Click-Through Rate - the percentage of people who clicked on your result after seeing it in search results (Clicks ÷ Impressions).
        """)
    
    with col2:
        st.markdown("""
        **CTR Potential**: The gap between your current CTR and the expected CTR for your ranking position. Higher values indicate optimization opportunities.
        
        **Traffic Potential**: Estimated additional monthly clicks you could gain by improving your CTR for this keyword.
        
        **Est. Monthly Volume**: Estimated total monthly search volume for this keyword across all websites.
        
        **Keyword Difficulty (KD)**: Estimated difficulty (0-100) to rank well for this keyword:
        - **0-20**: Very Easy
        - **21-40**: Easy  
        - **41-60**: Medium
        - **61-80**: Hard
        - **81-100**: Very Hard
        
        **Average CPC**: Estimated cost per click if you were to advertise for this keyword in Google Ads.
        
        **Search Intent**: The likely purpose behind the search query.
        """)
    
    # Opportunity Types
    st.subheader("Opportunity Types")
    st.markdown("""
    **CTR Optimization**: Keywords where you rank in top 3 but have low click-through rates. Focus on improving titles and meta descriptions.
    
    **Top 3 Push**: Keywords ranking 4-10 that could realistically be pushed into the top 3 with optimization effort.
    
    **Top 10 Push**: Keywords ranking 11-20 that could realistically be pushed into the top 10 with some effort.
    
    **First Page Push**: Keywords ranking 21+ that could potentially reach the first page (positions 1-20).
    
    **Long-term Target**: Lower priority keywords that require significant effort but may pay off over time.
    """)
    
    # Priority Levels
    st.subheader("Priority Levels")
    st.markdown("""
    **High Priority**: Keywords with Opportunity Score 70+ that should be addressed immediately for quick wins.
    
    **Medium Priority**: Keywords with Opportunity Score 40-69 that represent good opportunities with moderate effort required.
    
    **Low Priority**: Keywords with Opportunity Score <40 that are long-term targets requiring significant investment.
    """)
    
    # Search Intent Types  
    st.subheader("Search Intent Types")
    st.markdown("""
    **Informational**: Users seeking information (how-to, what is, why does, etc.).
    
    **Navigational**: Users looking for a specific website or brand.
    
    **Commercial**: Users researching products/services before buying (best, review, compare, vs).
    
    **Transactional**: Users ready to take action (buy, sign up, hire, subscribe).
    """)
    
    # Opportunity Score Calculation
    st.subheader("Opportunity Score Calculation")
    st.markdown("""
    The Opportunity Score is calculated using four weighted factors:
    
    - **Position Score (40%)**: Higher ranking positions receive higher scores
    - **Volume Score (30%)**: Real search volume from Ahrefs (when available) or estimated from impressions
    - **Difficulty Score (20%)**: Lower keyword difficulty scores get higher opportunity scores
    - **Traffic Score (10%)**: Expected jump in CTR for 1 position improvement
    
    **Data Sources**: We prioritize real Ahrefs data (marked as "Ahrefs") when available, falling back to GSC estimates (marked as "GSC Est.") for comprehensive coverage.
    
    This creates a balanced score that prioritizes keywords with the best combination of existing visibility, real search volume, feasibility, and optimization opportunity.
    """)
    
    # CTR Benchmarks
    st.subheader("CTR Benchmarks by Position")
    st.markdown("""
    **Average Click-Through Rates by Search Position:**
    - Position 1: ~31% CTR
    - Position 2: ~24% CTR  
    - Position 3: ~18% CTR
    - Position 4: ~13% CTR
    - Position 5: ~9% CTR
    - Position 10: ~2% CTR
    
    If your CTR is significantly below these benchmarks for your position, there's likely an optimization opportunity through better titles, meta descriptions, or rich snippets.
    """)

if __name__ == "__main__":
    main()
    display_glossary() 