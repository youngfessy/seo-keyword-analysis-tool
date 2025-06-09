#!/usr/bin/env python3
"""
GSC-Only Keyword Analyzer for synthesis.com/tutor

Analyzes Google Search Console data to identify:
- Non-brand keywords ranking in top 100
- Opportunity scoring based on position, impressions, CTR
- Export capabilities for further analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import config
from gsc_client import GSCClient
from typing import List, Dict, Any
import re

class KeywordOpportunity:
    """Data class for keyword opportunities."""
    
    def __init__(self, keyword_data: Dict[str, Any]):
        self.keyword = keyword_data['query']
        self.average_position = keyword_data['position']
        self.impressions = keyword_data['impressions']
        self.clicks = keyword_data['clicks']
        self.ctr = keyword_data['ctr']
        
        # Calculate derived metrics
        self.ctr_potential = self._calculate_ctr_potential()
        self.traffic_potential = self._calculate_traffic_potential()
        self.opportunity_score = self._calculate_opportunity_score()
        self.opportunity_type = self._determine_opportunity_type()
        self.priority = self._determine_priority()
    
    def _calculate_ctr_potential(self) -> float:
        """Calculate CTR potential based on position."""
        # Expected CTR by position (industry averages)
        expected_ctrs = {
            1: 0.31, 2: 0.24, 3: 0.18, 4: 0.13, 5: 0.09,
            6: 0.06, 7: 0.04, 8: 0.03, 9: 0.025, 10: 0.02
        }
        
        position = min(int(self.average_position), 10)
        expected_ctr = expected_ctrs.get(position, 0.01)
        
        # Return the gap between expected and actual CTR
        return max(0, expected_ctr - self.ctr)
    
    def _calculate_traffic_potential(self) -> int:
        """Calculate potential additional traffic."""
        return int(self.impressions * self.ctr_potential)
    
    def _calculate_opportunity_score(self) -> float:
        """Calculate overall opportunity score (0-100)."""
        # Position score (closer to top = higher score)
        position_score = max(0, (101 - self.average_position) / 100) * 40
        
        # Traffic volume score
        volume_score = min(np.log10(max(1, self.impressions)) / 4, 1) * 30
        
        # CTR gap score
        ctr_score = min(self.ctr_potential * 100, 1) * 20
        
        # Click potential score  
        click_score = min(self.traffic_potential / 100, 1) * 10
        
        return min(100, position_score + volume_score + ctr_score + click_score)
    
    def _determine_opportunity_type(self) -> str:
        """Determine the type of opportunity."""
        if self.average_position <= 3 and self.ctr < 0.15:
            return "CTR Optimization"
        elif 4 <= self.average_position <= 10 and self.impressions >= 100:
            return "Top 10 Push"
        elif 11 <= self.average_position <= 20 and self.impressions >= 50:
            return "First Page Push"
        elif 21 <= self.average_position <= 50:
            return "Content Optimization"
        else:
            return "Long-term Target"
    
    def _determine_priority(self) -> str:
        """Determine priority level."""
        if self.opportunity_score >= 70:
            return "High"
        elif self.opportunity_score >= 40:
            return "Medium"
        else:
            return "Low"


class GSCKeywordAnalyzer:
    """Google Search Console keyword analyzer."""
    
    def __init__(self):
        self.gsc_client = GSCClient()
        self.brand_keywords = config.BRAND_KEYWORDS
        self.target_domain = config.TARGET_DOMAIN
        
    def is_brand_keyword(self, keyword: str) -> bool:
        """Check if a keyword contains brand terms."""
        keyword_lower = keyword.lower()
        return any(brand.lower() in keyword_lower for brand in self.brand_keywords)
    
    def get_keyword_data(self, days_back: int = 90) -> pd.DataFrame:
        """Fetch and process GSC keyword data."""
        print(f"📊 Fetching GSC data for last {days_back} days...")
        
        # Authenticate first
        if not self.gsc_client.authenticate():
            print("❌ Failed to authenticate with Google Search Console")
            return pd.DataFrame()
        
        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        # Fetch GSC data
        df_raw = self.gsc_client.get_search_analytics_data(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        if df_raw.empty:
            print("❌ No GSC data retrieved")
            return pd.DataFrame()
        
        print(f"✅ Retrieved {len(df_raw)} total keywords from GSC")
        
        # Apply filters
        df_filtered = self._apply_filters(df_raw)
        print(f"📝 After filtering: {len(df_filtered)} keywords")
        
        return df_filtered
    
    def _apply_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply filtering criteria to the keyword data."""
        # Filter out brand keywords
        df = df[~df['query'].apply(self.is_brand_keyword)]
        print(f"   📛 Removed brand keywords: {len(df)} remaining")
        
        # Filter by position (top 100)
        df = df[df['position'] <= config.MAX_POSITION]
        print(f"   📍 Top {config.MAX_POSITION} positions: {len(df)} remaining")
        
        # Filter by minimum impressions
        df = df[df['impressions'] >= config.MIN_IMPRESSIONS]
        print(f"   👁️ Min {config.MIN_IMPRESSIONS} impressions: {len(df)} remaining")
        
        # Remove very short keywords (likely not meaningful)
        df = df[df['query'].str.len() >= 3]
        print(f"   📏 Min 3 characters: {len(df)} remaining")
        
        # Sort by opportunity potential
        df = df.sort_values(['position', 'impressions'], ascending=[True, False])
        
        return df.reset_index(drop=True)
    
    def analyze_opportunities(self, df: pd.DataFrame) -> List[KeywordOpportunity]:
        """Analyze keyword opportunities."""
        print("🔍 Analyzing keyword opportunities...")
        
        opportunities = []
        for _, row in df.iterrows():
            opportunity = KeywordOpportunity(row.to_dict())
            opportunities.append(opportunity)
        
        # Sort by opportunity score
        opportunities.sort(key=lambda x: x.opportunity_score, reverse=True)
        
        return opportunities
    
    def categorize_opportunities(self, opportunities: List[KeywordOpportunity]) -> Dict[str, List[KeywordOpportunity]]:
        """Categorize opportunities by type and priority."""
        categories = {
            'High Priority': [],
            'Medium Priority': [],
            'Low Priority': [],
            'CTR Optimization': [],
            'Top 10 Push': [],
            'First Page Push': [],
            'Content Optimization': [],
            'Long-term Target': []
        }
        
        for opp in opportunities:
            # Add to priority categories
            categories[f"{opp.priority} Priority"].append(opp)
            
            # Add to opportunity type categories
            categories[opp.opportunity_type].append(opp)
        
        return categories
    
    def export_to_csv(self, opportunities: List[KeywordOpportunity], filename: str = None) -> str:
        """Export opportunities to CSV file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"keyword_opportunities_{timestamp}.csv"
        
        # Create export data
        export_data = []
        for opp in opportunities:
            export_data.append({
                'Keyword': opp.keyword,
                'Current Position': round(opp.average_position, 1),
                'Monthly Impressions': opp.impressions,
                'Monthly Clicks': opp.clicks,
                'Current CTR': f"{opp.ctr:.2%}",
                'CTR Potential': f"{opp.ctr_potential:.2%}",
                'Traffic Potential': opp.traffic_potential,
                'Opportunity Score': round(opp.opportunity_score, 1),
                'Opportunity Type': opp.opportunity_type,
                'Priority': opp.priority
            })
        
        df_export = pd.DataFrame(export_data)
        df_export.to_csv(filename, index=False)
        
        print(f"📁 Exported {len(opportunities)} opportunities to {filename}")
        return filename
    
    def print_summary(self, opportunities: List[KeywordOpportunity]):
        """Print analysis summary."""
        if not opportunities:
            print("❌ No opportunities found")
            return
        
        categories = self.categorize_opportunities(opportunities)
        
        print("\n" + "="*60)
        print("📈 KEYWORD OPPORTUNITY ANALYSIS SUMMARY")
        print("="*60)
        
        print(f"🎯 Target Domain: {self.target_domain}")
        print(f"📊 Total Non-Brand Keywords Analyzed: {len(opportunities)}")
        
        # Priority breakdown
        print(f"\n🏆 PRIORITY BREAKDOWN:")
        print(f"   High Priority: {len(categories['High Priority'])} keywords")
        print(f"   Medium Priority: {len(categories['Medium Priority'])} keywords") 
        print(f"   Low Priority: {len(categories['Low Priority'])} keywords")
        
        # Opportunity type breakdown
        print(f"\n🎯 OPPORTUNITY TYPES:")
        for opp_type in ['CTR Optimization', 'Top 10 Push', 'First Page Push', 'Content Optimization', 'Long-term Target']:
            count = len(categories[opp_type])
            if count > 0:
                print(f"   {opp_type}: {count} keywords")
        
        # Top opportunities
        print(f"\n🥇 TOP 10 OPPORTUNITIES:")
        print("-" * 60)
        for i, opp in enumerate(opportunities[:10], 1):
            print(f"{i:2d}. {opp.keyword}")
            print(f"     Position: {opp.average_position:.1f} | Score: {opp.opportunity_score:.1f} | {opp.opportunity_type}")
        
        # Traffic potential summary
        total_traffic_potential = sum(opp.traffic_potential for opp in opportunities)
        print(f"\n📈 TOTAL TRAFFIC POTENTIAL: {total_traffic_potential:,} additional monthly clicks")
        
        print("="*60)


def main():
    """Main execution function."""
    print("🔍 GSC Keyword Opportunity Analyzer for synthesis.com/tutor")
    print("="*60)
    
    try:
        # Initialize analyzer
        analyzer = GSCKeywordAnalyzer()
        
        # Fetch and analyze data
        df = analyzer.get_keyword_data(days_back=config.DAYS_BACK)
        
        if df.empty:
            print("❌ No data to analyze")
            return
        
        # Analyze opportunities
        opportunities = analyzer.analyze_opportunities(df)
        
        # Print summary
        analyzer.print_summary(opportunities)
        
        # Export to CSV
        export_file = analyzer.export_to_csv(opportunities)
        
        print(f"\n✅ Analysis complete! Check {export_file} for detailed data.")
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        raise


if __name__ == "__main__":
    main() 