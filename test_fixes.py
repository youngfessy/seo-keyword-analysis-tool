#!/usr/bin/env python3
"""
Test script to verify the opportunity type and search volume fixes
"""

from ahrefs_data_loader import get_real_search_volume, has_ahrefs_data
from keyword_analyzer import KeywordOpportunity

def test_opportunity_types():
    """Test opportunity type classification."""
    print("🧪 Testing Opportunity Type Classification...")
    
    test_cases = [
        # Format: (position, impressions, ctr, expected_type)
        (2.5, 1000, 0.10, "CTR Optimization"),  # Top 3, low CTR
        (5.0, 500, 0.25, "Top 3 Push"),       # Position 4-10, good traffic
        (15.0, 200, 0.15, "Top 10 Push"),     # Position 11-20
        (25.0, 100, 0.10, "First Page Push"), # Position 21+
        (50.0, 20, 0.05, "Long-term Target")  # Very low position
    ]
    
    for position, impressions, ctr, expected in test_cases:
        keyword_data = {
            'query': 'test keyword',
            'position': position,
            'impressions': impressions,
            'clicks': int(impressions * ctr),
            'ctr': ctr
        }
        
        opportunity = KeywordOpportunity(keyword_data)
        actual = opportunity.opportunity_type
        
        status = "✅" if actual == expected else "❌"
        print(f"  {status} Position {position} → Expected: {expected}, Got: {actual}")

def test_search_volume():
    """Test search volume calculation."""
    print("\n📊 Testing Search Volume Calculation...")
    
    # Test with a keyword that has Ahrefs data
    test_keyword = "math tutor"  # Should be in our Ahrefs data
    impressions = 100
    
    volume = get_real_search_volume(test_keyword, impressions)
    has_data = has_ahrefs_data(test_keyword)
    
    print(f"  Keyword: '{test_keyword}'")
    print(f"  Has Ahrefs data: {has_data}")
    print(f"  Impressions: {impressions:,}")
    print(f"  Calculated volume: {volume:,}")
    
    # Test that volume is at least as high as impressions
    if volume >= impressions:
        print("  ✅ Volume >= Impressions (logical)")
    else:
        print("  ❌ Volume < Impressions (illogical)")
    
    # Test with a keyword that likely doesn't have Ahrefs data
    test_keyword2 = "very specific niche keyword that probably doesnt exist"
    volume2 = get_real_search_volume(test_keyword2, impressions)
    has_data2 = has_ahrefs_data(test_keyword2)
    
    print(f"\n  Keyword: '{test_keyword2}'")
    print(f"  Has Ahrefs data: {has_data2}")
    print(f"  Impressions: {impressions:,}")
    print(f"  Calculated volume: {volume2:,}")
    print(f"  Multiplier used: {volume2 / impressions:.1f}x")

if __name__ == "__main__":
    print("🔧 Testing Fixes for SEO Dashboard Issues")
    print("=" * 50)
    
    test_opportunity_types()
    test_search_volume()
    
    print("\n✅ Testing complete!") 