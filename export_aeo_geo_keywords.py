#!/usr/bin/env python3
"""
Export unique keywords from AEO/GEO dashboard for Ahrefs analysis
"""

import pandas as pd
from gsc_client import GSCClient
import config
from datetime import datetime, timedelta
import re

def export_aeo_geo_keywords():
    """Fetch and export unique keywords from AEO/GEO analysis."""
    try:
        print("🔍 Fetching Google Search Console data for AEO/GEO export...")
        
        # Initialize GSC client
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
            print("❌ No data retrieved from GSC")
            return
        
        # Filter for non-brand keywords
        brand_keywords = config.BRAND_KEYWORDS
        brand_pattern = '|'.join([re.escape(brand.lower()) for brand in brand_keywords])
        df_filtered = df[~df['query'].str.lower().str.contains(brand_pattern, na=False)]
        
        # Create keyword export with just the unique keywords
        keywords_df = pd.DataFrame({
            'keyword': df_filtered['query'].unique()
        })
        
        print(f'📊 Loaded {len(df)} total queries, {len(df_filtered)} non-brand queries, {len(keywords_df)} unique keywords')
        
        # Export for Ahrefs
        export_file = 'aeo_geo_keywords_for_ahrefs.csv'
        keywords_df.to_csv(export_file, index=False)
        print(f'✅ Exported AEO/GEO keywords to: {export_file}')
        
        return export_file
        
    except Exception as e:
        print(f"❌ Error exporting AEO/GEO keywords: {str(e)}")
        return None

if __name__ == "__main__":
    export_aeo_geo_keywords() 