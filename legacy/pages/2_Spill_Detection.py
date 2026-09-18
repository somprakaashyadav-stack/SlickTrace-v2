import streamlit as st
import time
import numpy as np
from PIL import Image

st.set_page_config(page_title="Spill Detection", page_icon="🛰️", layout="wide")

st.title("Spill Detection 🛰️")
st.markdown("Upload Sentinel-1 SAR imagery to detect oil spills using the U-Net model.")

uploaded_file = st.file_uploader("Upload SAR Image (PNG, JPG, TIFF)", type=["png", "jpg", "jpeg", "tif", "tiff"])

if uploaded_file is not None:
    st.success("Image successfully loaded.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Original SAR Imagery")
        # In a real scenario, this would be a high-res SAR image
        image = Image.open(uploaded_file)
        st.image(image, caption="Input Image", use_column_width=True)
        
    with col2:
        st.markdown("### Detection Result (U-Net)")
        if st.button("Run Segmentation"):
            with st.spinner("Processing image through DeepLabV3+/U-Net..."):
                time.sleep(2) # Mock processing time
                
                # Create a mock segmented output
                img_array = np.array(image)
                # Mock highlighting some area as oil spill (dark patch)
                st.success("Oil spill detected!")
                st.image(image, caption="Detected Spill Boundary (Polygon)", use_column_width=True) # Replace with real segmented image later
                
                st.markdown("""
                **Detection Details:**
                * **Coordinates:** Lat: 27.512, Lon: -90.015
                * **Calculated Area:** 12.4 km²
                * **Confidence Score:** 94.2%
                * **Timestamp (T):** 2026-09-17 08:30:00 UTC
                """)
                
                st.info("Proceed to Step 3 (Hindcasting) to simulate the backward drift of this spill.")
