import streamlit as st

st.set_page_config(page_title="Reporting", page_icon="📑", layout="wide")

st.title("Reporting & Export 📑")
st.markdown("Generate official reports for environmental agencies and maritime authorities.")

st.markdown("### Investigation Summary: SP-2026-09-17-A")

st.text_area("Executive Summary", value="""On 2026-09-17 08:30:00 UTC, a 12.4 km² oil spill was detected in the Gulf of Mexico (Lat: 27.512, Lon: -90.015) via Sentinel-1 SAR imagery.
Backward drift simulations (hindcasting) over 24 hours identified the origin window as 2026-09-16 between 08:30 and 10:30 UTC at coordinates (27.850, -89.500).
AIS correlation identified 3 vessels in the vicinity. Behavioral analysis flags NORDIC TRADER (MMSI: 257894000) as the primary suspect (Guilt Score: 92%) due to an anomalous speed drop (to 3.1 knots) and a subsequent 15-minute AIS gap exactly at the simulated origin.
""", height=150)

col1, col2, col3 = st.columns(3)
with col1:
    st.checkbox("Include SAR Imagery", value=True)
with col2:
    st.checkbox("Include Hindcast Map", value=True)
with col3:
    st.checkbox("Include AIS Behavioral Charts", value=True)

if st.button("Generate Official Report (PDF)"):
    st.success("Report generated successfully! (Mock)")
    st.download_button(label="Download PDF Report", data=b"mock pdf content", file_name="Investigation_Report_SP-2026-09-17-A.pdf", mime="application/pdf")
