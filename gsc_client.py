#!/usr/bin/env python3
"""
Google Search Console API client for fetching search performance data.
"""

import os
import pickle
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import pandas as pd
import config

class GSCClient:
    """Google Search Console API client."""
    
    def __init__(self):
        self.service = None
        self.credentials = None
        
    def authenticate(self):
        """Authenticate with Google Search Console API."""
        print("🔐 Authenticating with Google Search Console API...")
        
        # Check if we have stored credentials
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.credentials = pickle.load(token)
        
        # If there are no valid credentials, get new ones
        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                print("  🔄 Refreshing expired credentials...")
                self.credentials.refresh(Request())
            else:
                print("  🆕 Getting new credentials...")
                # Create OAuth flow
                flow = Flow.from_client_config(
                    {
                        "web": {
                            "client_id": config.GOOGLE_CLIENT_ID,
                            "client_secret": config.GOOGLE_CLIENT_SECRET,
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "redirect_uris": ["http://localhost:8080"]
                        }
                    },
                    scopes=config.SCOPES
                )
                flow.redirect_uri = 'http://localhost:8080'
                
                # Get authorization URL
                auth_url, _ = flow.authorization_url(prompt='consent')
                
                print(f"\n🌐 Please visit this URL to authorize the application:")
                print(f"  {auth_url}")
                print(f"\n📋 After authorization, copy the authorization code from the URL:")
                
                # Get authorization code from user
                auth_code = input("Enter the authorization code: ").strip()
                
                # Exchange code for credentials
                flow.fetch_token(code=auth_code)
                self.credentials = flow.credentials
            
            # Save credentials for next time
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.credentials, token)
                print("  💾 Credentials saved for future use")
        
        # Build the service
        self.service = build(
            config.API_SERVICE_NAME, 
            config.API_VERSION, 
            credentials=self.credentials
        )
        print("  ✅ Successfully authenticated with Google Search Console")
        return True
    
    def get_search_analytics_data(self, start_date=None, end_date=None):
        """
        Fetch search analytics data from Google Search Console.
        
        Args:
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            
        Returns:
            pandas.DataFrame: Search analytics data
        """
        if not self.service:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        # Set default date range
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=config.DAYS_BACK)).strftime('%Y-%m-%d')
        
        print(f"📊 Fetching Search Console data from {start_date} to {end_date}...")
        
        # Prepare the request
        request = {
            'startDate': start_date,
            'endDate': end_date,
            'dimensions': ['query'],
            'rowLimit': 25000,  # Maximum allowed
            'startRow': 0
        }
        
        # Execute the request
        try:
            response = self.service.searchanalytics().query(
                siteUrl=f'sc-domain:{config.TARGET_DOMAIN.replace("/tutor", "")}',
                body=request
            ).execute()
            
            # Process the response
            if 'rows' not in response:
                print("  ⚠️ No data found in the specified date range")
                return pd.DataFrame()
            
            # Convert to DataFrame
            data = []
            for row in response['rows']:
                data.append({
                    'query': row['keys'][0],
                    'clicks': row['clicks'],
                    'impressions': row['impressions'],
                    'ctr': row['ctr'],
                    'position': row['position']
                })
            
            df = pd.DataFrame(data)
            print(f"  📈 Retrieved {len(df)} keywords from Search Console")
            
            return df
            
        except Exception as e:
            print(f"  ❌ Error fetching data: {str(e)}")
            return pd.DataFrame()
    
    def filter_data(self, df):
        """
        Filter the data based on our analysis criteria.
        
        Args:
            df (pandas.DataFrame): Raw search console data
            
        Returns:
            pandas.DataFrame: Filtered data
        """
        if df.empty:
            return df
        
        print("🔍 Filtering data based on criteria...")
        initial_count = len(df)
        
        # Filter by position (top 100 only)
        df = df[df['position'] <= config.MAX_POSITION]
        print(f"  📍 After position filter (≤{config.MAX_POSITION}): {len(df)} keywords")
        
        # Filter by minimum impressions
        df = df[df['impressions'] >= config.MIN_IMPRESSIONS]
        print(f"  👀 After impressions filter (≥{config.MIN_IMPRESSIONS}): {len(df)} keywords")
        
        # Filter out brand keywords
        def is_brand_keyword(query):
            query_lower = query.lower()
            return any(brand.lower() in query_lower for brand in config.BRAND_KEYWORDS)
        
        df = df[~df['query'].apply(is_brand_keyword)]
        print(f"  🏷️ After brand keyword filter: {len(df)} keywords")
        
        print(f"  ✅ Filtered from {initial_count} to {len(df)} keywords")
        return df

# Test function
def test_gsc_connection():
    """Test the Google Search Console connection."""
    client = GSCClient()
    if client.authenticate():
        print("✅ GSC authentication test passed!")
        return True
    else:
        print("❌ GSC authentication test failed!")
        return False

if __name__ == "__main__":
    test_gsc_connection() 