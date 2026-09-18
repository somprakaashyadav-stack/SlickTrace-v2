import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import time

st.set_page_config(page_title="Suspect Analysis", page_icon="📊", layout="wide")

st.title("Behavior Analysis & Suspect Scoring 📊")
st.markdown("Analyze the historical behavior of shortlisted vessels to identify anomalies such as sudden speed drops, erratic turns, or AIS gaps.")

vessel_options = ["NORDIC TRADER (MMSI: 257894000)", "OCEAN STAR (MMSI: 311000123)", "PACIFIC GULL (MMSI: 477999888)"]
selected_vessel = st.selectbox("Select Vessel for Deep Analysis", vessel_options)

if st.button("Run Scoring Algorithm"):
    with st.spinner("Analyzing SOG (Speed Over Ground), COG (Course Over Ground), and AIS transmission gaps..."):
        time.sleep(2)
        
        st.subheader("Suspect #1: NORDIC TRADER (MMSI: 257894000)")
        
        # Display Guilt Score
        score = 92
        st.markdown(f"### Guilt Score: <span style='color:red'>{score}% Match</span>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Speed Over Ground (SOG) Analysis")
            # Mock SOG data
            times = pd.date_range("2026-09-16 07:00", "2026-09-16 11:00", freq="10min")
            sog = np.random.normal(12, 0.5, len(times))
            # Create speed drop anomaly around 09:15
            sog[13:16] = [6.2, 3.1, 5.5] 
            
            df_sog = pd.DataFrame({"Time": times, "Speed (knots)": sog})
            fig = px.line(df_sog, x="Time", y="Speed (knots)", title="Vessel Speed Over Time")
            fig.add_vrect(x0="2026-09-16 09:10", x1="2026-09-16 09:30", fillcolor="red", opacity=0.2, annotation_text="Origin Window")
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.markdown("#### Behavioral Anomalies Detected")
            st.error("🚨 **Significant Speed Drop:** Vessel slowed from 12 knots to 3.1 knots exactly at the Origin Window.")
            st.warning("⚠️ **AIS Gap:** Transmission lost for 15 minutes immediately following the speed drop.")
            st.info("ℹ️ **Course Deviation:** Minor erratic turning observed during the slow down phase.")
            
        st.success("Analysis complete. This vessel is the primary suspect. Proceed to Reporting.")
