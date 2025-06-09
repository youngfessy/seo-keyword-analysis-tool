import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Google Search Console API Configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

# Analysis Configuration
TARGET_DOMAIN = 'synthesis.com/tutor'
BRAND_KEYWORDS = ['synthesis', 'synthesis tutor', 'synthsis', 'syntesis', 'synthesis.com']

# Search Console API Settings
SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']
API_SERVICE_NAME = 'searchconsole'
API_VERSION = 'v1'

# Analysis Parameters
MAX_POSITION = 100  # Only analyze keywords ranking in top 100
DAYS_BACK = 90      # Analyze last 90 days of data
MIN_IMPRESSIONS = 10  # Minimum impressions to consider a keyword

# GSC-Based Opportunity Scoring Thresholds
OPPORTUNITY_THRESHOLDS = {
    'high': {'max_position': 10, 'min_impressions': 100, 'min_ctr_potential': 0.05},  # Top 10, good traffic potential
    'medium': {'max_position': 30, 'min_impressions': 50, 'min_ctr_potential': 0.02}, # Top 30, moderate potential
    'low': {'max_position': 100, 'min_impressions': 10, 'min_ctr_potential': 0.01}    # Top 100, basic potential
} 