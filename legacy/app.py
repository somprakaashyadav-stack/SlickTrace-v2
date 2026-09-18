import streamlit as st

st.set_page_config(
    page_title="SlickTrace v2",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("SlickTrace v2 🌊")
st.markdown("### Oil Spill Detection & Vessel Attribution Platform")

st.markdown("""
Welcome to **SlickTrace v2**. This platform provides an end-to-end automated pipeline for identifying marine oil spills and attributing them to the responsible vessels.

#### Workflow:
1. **Spill Detection**: Upload Sentinel-1 SAR imagery to detect oil spills using our U-Net model.
2. **Hindcasting**: Simulate backward drift using OpenDrift to find the temporal and spatial origin.
3. **AIS Correlation**: Filter AIS datasets to identify vessels present in the origin window.
4. **Suspect Analysis**: Analyze vessel behavior (speed, course, AIS gaps) to generate a guilt score.
5. **Reporting**: Generate comprehensive reports for authorities.

Please use the sidebar to navigate through the pipeline stages.
""")

# Dashboard preview on home page
st.info("Navigate to the **Dashboard** page to view active alerts and global statistics.")
