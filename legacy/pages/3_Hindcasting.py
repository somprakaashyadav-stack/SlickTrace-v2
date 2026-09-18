import streamlit as st
import folium
from streamlit_folium import st_folium
import time

st.set_page_config(page_title="Hindcasting & Trajectory", page_icon="🌊", layout="wide")

st.title("Backward Tracking / Hindcasting 🌊")
st.markdown("Use environmental data (ocean currents & wind) to simulate the oil drift backwards in time and find the origin window.")

st.sidebar.header("Simulation Parameters")
hours_back = st.sidebar.slider("Hours to Hindcast", min_value=1, max_value=72, value=24)
wind_data = st.sidebar.selectbox("Wind Data Source", ["ECMWF", "GFS"])
current_data = st.sidebar.selectbox("Current Data Source", ["Copernicus Marine Service", "HYCOM"])

st.markdown("### Spill Input Coordinates")
col_lat, col_lon, col_time = st.columns(3)
col_lat.text_input("Latitude", value="27.512")
col_lon.text_input("Longitude", value="-90.015")
col_time.text_input("Detection Time (UTC)", value="2026-09-17 08:30:00")

if st.button("Run OpenDrift Simulation"):
    with st.spinner("Fetching weather & ocean data, running OpenDrift simulation..."):
        time.sleep(3) # Mock simulation time
        
        st.success("Simulation Complete!")
        
        st.markdown(f"### Origin Window Found (-{hours_back} Hours)")
        st.info("**Origin Time:** 2026-09-16 08:30:00 UTC to 10:30:00 UTC\n\n**Origin Coordinates:** Lat: 27.850, Lon: -89.500")
        
        # Mock map showing trajectory
        m = folium.Map(location=[27.65, -89.75], zoom_start=9)
        
        # Spill Location
        folium.Marker(
            [27.512, -90.015], popup="Detected Spill", icon=folium.Icon(color="red", icon="warning-sign")
        ).add_to(m)
        
        # Origin Location
        folium.Marker(
            [27.850, -89.500], popup="Origin Window", icon=folium.Icon(color="green", icon="play")
        ).add_to(m)
        
        # Line connecting them
        folium.PolyLine(
            locations=[[27.512, -90.015], [27.6, -89.8], [27.7, -89.6], [27.850, -89.500]],
            color="orange", weight=3, opacity=0.8, tooltip="Drift Trajectory"
        ).add_to(m)
        
        st_folium(m, width=1200, height=500)
        
        st.info("Proceed to Step 4 (AIS Correlation) to find ships in the Origin Window.")
