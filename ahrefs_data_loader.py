#!/usr/bin/env python3
"""
Ahrefs Data Loader - Provides lookup functions for keyword data
Falls back to GSC/derived data when Ahrefs data is not available
"""

import pandas as pd
import glob
import os
from typing import Optional, Dict, Any
import streamlit as st

class AhrefsDataLoader:
    """Loads and provides lookup functions for Ahrefs keyword data."""
    
    def __init__(self):
        self.ahrefs_data = None
        self.keyword_lookup = {}
        self._load_ahrefs_data()
    
    def _load_ahrefs_data(self):
        """Load Ahrefs CSV files and create keyword lookup dictionary."""
        try:
            # Find all Ahrefs CSV files
            ahrefs_files = glob.glob('ahrefs_keyword_data/*.csv')
            
            if not ahrefs_files:
                print("⚠️ No Ahrefs data files found")
                return
            
            # Combine all Ahrefs files
            all_data = []
            for file in ahrefs_files:
                try:
                    df = pd.read_csv(file)
                    # Standardize column names (some might have different cases)
                    df.columns = df.columns.str.strip()
                    all_data.append(df)
                    print(f"✅ Loaded {len(df)} keywords from {os.path.basename(file)}")
                except Exception as e:
                    print(f"❌ Error loading {file}: {str(e)}")
                    continue
            
            if all_data:
                # Combine all dataframes
                self.ahrefs_data = pd.concat(all_data, ignore_index=True)
                
                # Remove duplicates, keeping the first occurrence
                self.ahrefs_data = self.ahrefs_data.drop_duplicates(subset=['Keyword'], keep='first')
                
                # Create lowercase keyword lookup for case-insensitive matching
                self.keyword_lookup = {}
                for idx, row in self.ahrefs_data.iterrows():
                    keyword_lower = str(row['Keyword']).lower().strip()
                    self.keyword_lookup[keyword_lower] = {
                        'volume': self._safe_int(row.get('Volume', 0)),
                        'difficulty': self._safe_int(row.get('Difficulty', 0)),
                        'cpc': self._safe_float(row.get('CPC', 0)),
                        'global_volume': self._safe_int(row.get('Global volume', 0)),
                        'traffic_potential': self._safe_int(row.get('Traffic potential', 0)),
                        'serp_features': str(row.get('SERP Features', '')),
                        'intents': str(row.get('Intents', ''))
                    }
                
                print(f"🎯 Successfully loaded {len(self.ahrefs_data)} unique keywords from Ahrefs")
                print(f"📊 Coverage: {len(self.keyword_lookup)} keywords indexed for lookup")
            
        except Exception as e:
            print(f"❌ Error loading Ahrefs data: {str(e)}")
            self.ahrefs_data = None
            self.keyword_lookup = {}
    
    def _safe_int(self, value):
        """Safely convert value to int, return 0 if conversion fails."""
        try:
            if pd.isna(value) or value == '':
                return 0
            return int(float(str(value).replace(',', '')))
        except (ValueError, TypeError):
            return 0
    
    def _safe_float(self, value):
        """Safely convert value to float, return 0.0 if conversion fails."""
        try:
            if pd.isna(value) or value == '':
                return 0.0
            return float(str(value).replace(',', ''))
        except (ValueError, TypeError):
            return 0.0
    
    def get_keyword_data(self, keyword: str) -> Dict[str, Any]:
        """
        Get comprehensive keyword data with Ahrefs data when available.
        Falls back to default values when not available.
        """
        keyword_lower = str(keyword).lower().strip()
        
        if keyword_lower in self.keyword_lookup:
            data = self.keyword_lookup[keyword_lower].copy()
            data['has_ahrefs_data'] = True
            return data
        else:
            # Return default/fallback data structure
            return {
                'volume': 0,
                'difficulty': 50,  # Default medium difficulty
                'cpc': 0.0,
                'global_volume': 0,
                'traffic_potential': 0,
                'serp_features': '',
                'intents': '',
                'has_ahrefs_data': False
            }
    
    def get_search_volume(self, keyword: str, fallback_impressions: int = 0) -> int:
        """Get real search volume from Ahrefs, fallback to impressions-based estimate."""
        data = self.get_keyword_data(keyword)
        
        if data['has_ahrefs_data'] and data['volume'] > 0:
            # Use real Ahrefs volume, but ensure it's at least as high as impressions
            # (since you can't get more impressions than total searches)
            return max(data['volume'], fallback_impressions)
        else:
            # Fallback to impressions-based estimation when no Ahrefs data
            # Use a more conservative multiplier (5x) instead of 10x
            return max(int(fallback_impressions * 5), fallback_impressions)
    
    def get_keyword_difficulty(self, keyword: str) -> int:
        """Get keyword difficulty from Ahrefs, fallback to estimated difficulty."""
        data = self.get_keyword_data(keyword)
        
        if data['has_ahrefs_data']:
            return data['difficulty']
        else:
            # Estimate difficulty based on keyword characteristics
            keyword_lower = keyword.lower()
            
            # Simple heuristic for difficulty estimation
            if len(keyword_lower.split()) >= 4:  # Long-tail
                return 30
            elif any(brand in keyword_lower for brand in ['synthesis', 'tutor', 'tutoring']):  # Brand terms
                return 20
            elif any(commercial in keyword_lower for commercial in ['best', 'top', 'review', 'compare']):  # Commercial
                return 70
            else:
                return 50  # Default medium difficulty
    
    def get_cpc(self, keyword: str) -> float:
        """Get cost per click from Ahrefs."""
        data = self.get_keyword_data(keyword)
        return data['cpc']
    
    def has_ahrefs_data(self, keyword: str) -> bool:
        """Check if keyword has Ahrefs data available."""
        keyword_lower = str(keyword).lower().strip()
        return keyword_lower in self.keyword_lookup
    
    def get_coverage_stats(self) -> Dict[str, int]:
        """Get statistics about Ahrefs data coverage."""
        return {
            'total_keywords': len(self.keyword_lookup) if self.keyword_lookup else 0,
            'has_volume': len([k for k, v in self.keyword_lookup.items() if v['volume'] > 0]) if self.keyword_lookup else 0,
            'has_difficulty': len([k for k, v in self.keyword_lookup.items() if v['difficulty'] > 0]) if self.keyword_lookup else 0,
            'has_cpc': len([k for k, v in self.keyword_lookup.items() if v['cpc'] > 0]) if self.keyword_lookup else 0
        }

# Global instance for easy access
@st.cache_resource
def get_ahrefs_loader():
    """Get cached Ahrefs data loader instance."""
    return AhrefsDataLoader()

# Convenience functions for easy access
def get_real_search_volume(keyword: str, fallback_impressions: int = 0) -> int:
    """Get real search volume with fallback."""
    loader = get_ahrefs_loader()
    return loader.get_search_volume(keyword, fallback_impressions)

def get_keyword_difficulty(keyword: str) -> int:
    """Get keyword difficulty with fallback."""
    loader = get_ahrefs_loader()
    return loader.get_keyword_difficulty(keyword)

def get_keyword_cpc(keyword: str) -> float:
    """Get keyword CPC."""
    loader = get_ahrefs_loader()
    return loader.get_cpc(keyword)

def has_ahrefs_data(keyword: str) -> bool:
    """Check if keyword has Ahrefs data."""
    loader = get_ahrefs_loader()
    return loader.has_ahrefs_data(keyword) 