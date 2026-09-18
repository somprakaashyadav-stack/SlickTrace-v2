import streamlit as st

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")

st.title("System Settings ⚙️")
st.markdown("Configure database connections, API keys, and model parameters.")

with st.expander("API Keys & External Services", expanded=True):
    st.text_input("Copernicus Marine Data API Key", type="password", value="********")
    st.text_input("ECMWF Wind Data API Key", type="password", value="********")

with st.expander("Database Configuration", expanded=True):
    st.text_input("AccessAIS Database URL / Path", value="sqlite:///data/accessais_sample.db")
    if st.button("Test Connection"):
        st.success("Connection to AccessAIS Database successful.")

with st.expander("Model Configurations", expanded=True):
    st.selectbox("Default Segmentation Model", ["U-Net (ResNet50 Backbone)", "DeepLabV3+"])
    st.slider("Spill Confidence Threshold (%)", 50, 100, 85)
