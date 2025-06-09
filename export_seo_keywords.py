#!/usr/bin/env python3
"""
Export unique keywords from SEO dashboard for Ahrefs analysis
"""

import pandas as pd
import glob
import os

def export_seo_keywords():
    """Export unique keywords from the latest SEO CSV."""
    # Load the latest SEO data
    csv_files = glob.glob('keyword_opportunities_*.csv')
    if not csv_files:
        print('❌ No SEO keyword opportunities CSV found')
        return
    
    latest_file = max(csv_files, key=os.path.getctime)
    df = pd.read_csv(latest_file)
    
    # Create keyword export with just the unique keywords
    keywords_df = pd.DataFrame({
        'keyword': df['Keyword'].unique()
    })
    
    print(f'📊 Loaded {len(df)} total rows, {len(keywords_df)} unique keywords from {latest_file}')
    
    # Export for Ahrefs
    export_file = 'seo_keywords_for_ahrefs.csv'
    keywords_df.to_csv(export_file, index=False)
    print(f'✅ Exported SEO keywords to: {export_file}')
    
    return export_file

if __name__ == "__main__":
    export_seo_keywords() 