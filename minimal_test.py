import streamlit as st

st.set_page_config(page_title="Minimal Test", page_icon="🧪")

st.title("🧪 Minimal Test App")
st.write("✅ If you can see this, basic Streamlit is working!")
st.success("🎉 App loaded successfully!")

st.sidebar.title("Test Sidebar")
st.sidebar.write("Sidebar is working!")

if st.button("Test Button"):
    st.balloons()
    st.write("🎈 Button clicked!")

st.metric("Test Metric", "42", "5")

st.write("Current time:", st.empty().write("App is running...")) 