#!/usr/bin/env python3
"""
Test script to verify configuration and API credentials are loaded correctly.
"""

import config

def test_configuration():
    """Test that all required configuration values are loaded."""
    print("🔧 Testing Configuration Setup...")
    print("=" * 50)
    
    # Test Google Search Console Config
    print("📊 Google Search Console API:")
    if config.GOOGLE_CLIENT_ID:
        print(f"  ✅ Client ID: {config.GOOGLE_CLIENT_ID[:20]}...")
    else:
        print("  ❌ Client ID: Not found")
    
    if config.GOOGLE_CLIENT_SECRET:
        print(f"  ✅ Client Secret: {config.GOOGLE_CLIENT_SECRET[:10]}...")
    else:
        print("  ❌ Client Secret: Not found")
    
    # Test Ahrefs Config
    print("\n🔗 Ahrefs API:")
    if config.AHREFS_API_TOKEN:
        print(f"  ✅ API Token: {config.AHREFS_API_TOKEN[:15]}...")
    else:
        print("  ❌ API Token: Not found")
    
    # Test Analysis Config
    print(f"\n🎯 Analysis Configuration:")
    print(f"  Target Domain: {config.TARGET_DOMAIN}")
    print(f"  Brand Keywords: {config.BRAND_KEYWORDS}")
    print(f"  Max Position: {config.MAX_POSITION}")
    print(f"  Days Back: {config.DAYS_BACK}")
    print(f"  Min Impressions: {config.MIN_IMPRESSIONS}")
    
    # Test Opportunity Thresholds
    print(f"\n📈 Opportunity Scoring:")
    for level, thresholds in config.OPPORTUNITY_THRESHOLDS.items():
        print(f"  {level.upper()}: Position ≤ {thresholds['max_position']}, Difficulty ≤ {thresholds['max_difficulty']}")
    
    print("\n" + "=" * 50)
    
    # Check if all required credentials are present
    missing_creds = []
    if not config.GOOGLE_CLIENT_ID:
        missing_creds.append("GOOGLE_CLIENT_ID")
    if not config.GOOGLE_CLIENT_SECRET:
        missing_creds.append("GOOGLE_CLIENT_SECRET")
    if not config.AHREFS_API_TOKEN:
        missing_creds.append("AHREFS_API_TOKEN")
    
    if missing_creds:
        print(f"❌ Missing credentials: {', '.join(missing_creds)}")
        print("Please check your .env file")
        return False
    else:
        print("✅ All credentials loaded successfully!")
        return True

if __name__ == "__main__":
    test_configuration() 