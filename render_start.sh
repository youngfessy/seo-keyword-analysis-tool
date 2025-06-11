#!/bin/bash
# Render startup script for SEO Analysis Suite

# Start the Streamlit app
streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true --server.enableCORS=false --server.enableXsrfProtection=false 