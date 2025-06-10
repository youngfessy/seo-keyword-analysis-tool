import streamlit as st

# Configure page - MUST be first Streamlit command
st.set_page_config(
    page_title="SEO Analysis Suite - Test",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Test version of the main application."""
    
    st.title("🧪 SEO Analysis Suite - Test Mode")
    st.success("✅ App is loading successfully!")
    
    # Sidebar navigation
    st.sidebar.title("📊 Test Mode")
    st.sidebar.markdown("**synthesis.com/tutor**")
    st.sidebar.markdown("---")
    
    # Test different components
    test_option = st.sidebar.selectbox(
        "Test Component:",
        ["Basic UI", "Import Test", "GSC Connection Test"]
    )
    
    if test_option == "Basic UI":
        st.write("✅ Basic Streamlit UI is working!")
        st.metric("Test Metric", "100", "10")
        
    elif test_option == "Import Test":
        st.write("🔍 Testing imports...")
        try:
            import pandas as pd
            st.success("✅ Pandas imported successfully")
        except Exception as e:
            st.error(f"❌ Pandas import failed: {e}")
            
        try:
            import plotly.express as px
            st.success("✅ Plotly imported successfully")
        except Exception as e:
            st.error(f"❌ Plotly import failed: {e}")
            
        try:
            from dashboard import load_latest_data
            st.success("✅ Dashboard module imported successfully")
        except Exception as e:
            st.error(f"❌ Dashboard import failed: {e}")
            
        try:
            from aeo_geo_dashboard import get_aeo_data_from_session
            st.success("✅ AEO dashboard module imported successfully")
        except Exception as e:
            st.error(f"❌ AEO dashboard import failed: {e}")
    
    elif test_option == "GSC Connection Test":
        st.write("🔐 Testing Google Search Console connection...")
        if st.button("Test GSC Authentication"):
            try:
                from gsc_client import GSCClient
                st.info("📡 Attempting to connect to Google Search Console...")
                
                gsc_client = GSCClient()
                gsc_client.authenticate()
                st.success("✅ Google Search Console authentication successful!")
                
            except Exception as e:
                st.error(f"❌ GSC connection failed: {e}")
                st.write("**Error details:**")
                st.code(str(e))

if __name__ == "__main__":
    main() 