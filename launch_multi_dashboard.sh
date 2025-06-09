#!/bin/bash

# Launch Multi-Dashboard for SEO/AEO/GEO Analysis
# This script starts the comprehensive dashboard with multiple tabs

echo "🚀 Starting Multi-Dashboard for SEO/AEO/GEO Analysis..."
echo "📊 Dashboard includes:"
echo "   - SEO: Traditional keyword opportunity analysis"
echo "   - AEO/GEO: Answer Engine & Generative Engine Optimization"
echo ""
echo "🌐 Dashboard will open in your browser automatically"
echo "💡 Use Ctrl+C to stop the dashboard"
echo ""

# Make sure we're in the right directory
cd "$(dirname "$0")"

# Check if required files exist
if [ ! -f "multi_dashboard.py" ]; then
    echo "❌ Error: multi_dashboard.py not found"
    exit 1
fi

if [ ! -f "gsc_client.py" ]; then
    echo "❌ Error: gsc_client.py not found"
    exit 1
fi

if [ ! -f "config.py" ]; then
    echo "❌ Error: config.py not found"
    exit 1
fi

# Launch the dashboard
streamlit run multi_dashboard.py --server.port 8502 