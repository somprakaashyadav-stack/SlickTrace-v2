import streamlit as st
import pandas as pd
import time

st.set_page_config(page_title="AIS Correlation", page_icon="🚢", layout="wide")

st.title("AIS Correlation 🚢")
st.markdown("Query the AccessAIS database to find vessels that crossed the Origin Window.")

st.markdown("### Origin Window Parameters")
col1, col2 = st.columns(2)
with col1:
    st.text_input("Start Time (UTC)", value="2026-09-16 08:30:00", disabled=True)
    st.text_input("Origin Lat", value="27.850", disabled=True)
with col2:
    st.text_input("End Time (UTC)", value="2026-09-16 10:30:00", disabled=True)
    st.text_input("Origin Lon", value="-89.500", disabled=True)

st.sidebar.header("Filter Settings")
st.sidebar.slider("Buffer Radius (km)", 1, 50, 10)
st.sidebar.multiselect("Vessel Types", ["Tanker", "Cargo", "Fishing", "Passenger"], default=["Tanker", "Cargo"])

if st.button("Query AccessAIS Database"):
    with st.spinner("Executing spatial-temporal query on AccessAIS..."):
        time.sleep(2)
        
        # Mock dataset of shortlisted vessels
        vessels = [
            {"Vessel Name": "NORDIC TRADER", "MMSI": "257894000", "Type": "Tanker", "Proximity (km)": 1.2, "Time in Zone": "09:15:00"},
            {"Vessel Name": "OCEAN STAR", "MMSI": "311000123", "Type": "Cargo", "Proximity (km)": 3.5, "Time in Zone": "09:42:00"},
            {"Vessel Name": "PACIFIC GULL", "MMSI": "477999888", "Type": "Tanker", "Proximity (km)": 8.0, "Time in Zone": "10:10:00"}
        ]
        df_vessels = pd.DataFrame(vessels)
        
        st.success(f"Found {len(df_vessels)} candidate vessels in the origin window.")
        
        st.dataframe(df_vessels, use_container_width=True)
        
        st.info("Proceed to Step 5 (Suspect Analysis) to run behavioral algorithms and assign a Guilt Score.")
