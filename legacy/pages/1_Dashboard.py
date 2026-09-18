import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np

st.set_page_config(page_title="Dashboard", page_icon="🏠", layout="wide")

st.title("Dashboard 🏠")
st.markdown("Overview of recent oil spill alerts and active investigations.")

# Mock data for recent spills
data = {
    "Spill ID": ["SP-2026-09-17-A", "SP-2026-09-16-B", "SP-2026-09-15-C"],
    "Date Detected": ["2026-09-17", "2026-09-16", "2026-09-15"],
    "Location": ["Gulf of Mexico", "North Sea", "Mediterranean"],
    "Lat": [27.5, 56.0, 35.5],
    "Lon": [-90.0, 3.0, 15.0],
    "Status": ["Investigating", "Suspect Identified", "Closed"],
    "Severity": ["High", "Medium", "Low"]
}
df = pd.DataFrame(data)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Active Alerts", "2")
with col2:
    st.metric("Suspects Identified (30 Days)", "5")
with col3:
    st.metric("Total Area Monitored", "1.2M sq km")

st.markdown("### Recent Spills Map")

m = folium.Map(location=[40, 0], zoom_start=2)
for idx, row in df.iterrows():
    color = "red" if row["Severity"] == "High" else "orange" if row["Severity"] == "Medium" else "green"
    folium.Marker(
        location=[row["Lat"], row["Lon"]],
        popup=f"{row['Spill ID']} - {row['Status']}",
        icon=folium.Icon(color=color, icon="info-sign")
    ).add_to(m)

st_folium(m, width=1200, height=400)

st.markdown("### Recent Alerts List")
st.dataframe(df.drop(columns=["Lat", "Lon"]), use_container_width=True)
