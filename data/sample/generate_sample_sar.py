"""
Deterministic Generator for Sample SAR Granule
Generates 64x64 raw backscatter intensity matrix representing a Sentinel-1 IW SAR image.
Includes multiplicative speckle noise, coastal land boundary, and a dark spot oil slick.
"""
import json
import numpy as np
from pathlib import Path

np.random.seed(42)

OUTPUT_DIR = Path(__file__).resolve().parent

def generate_sar_scene():
    height, width = 64, 64
    
    # Base ocean clutter (mean backscatter intensity ~ 0.15)
    mean_ocean = 0.15
    ocean = np.random.gamma(shape=4.0, scale=mean_ocean/4.0, size=(height, width))
    
    # 1. Add coastal land mask in top-right corner (rows < 15 and cols > 45)
    land_mask = np.zeros((height, width), dtype=bool)
    for r in range(height):
        for c in range(width):
            if r < 15 and c > 45:
                land_mask[r, c] = True
                ocean[r, c] = 0.8 + np.random.normal(0, 0.05) # High land backscatter
                
    # 2. Add oil slick dark spot in center (rows 25:40, cols 20:42)
    slick_mask = np.zeros((height, width), dtype=bool)
    for r in range(25, 40):
        for c in range(20, 42):
            # Elongated slick shape attenuation (backscatter drops to ~0.02)
            dist_center = ((r - 32)/7.5)**2 + ((c - 31)/11.0)**2
            if dist_center <= 1.0:
                slick_mask[r, c] = True
                attenuation = 0.15 # Strong backscatter damping by oil film
                ocean[r, c] = ocean[r, c] * attenuation

    sar_data = {
        "scene_id": "S1B_IW_GRDH_1SDV_20260912T143000_MUMBAI",
        "satellite": "Sentinel-1B",
        "sensor": "C-Band SAR (IW)",
        "acquisition_time": "2026-09-12T14:30:00Z",
        "polarization": "VV",
        "resolution_m": 10.0,
        "dimensions": [height, width],
        "center_coordinates": {"latitude": 18.9100, "longitude": 72.3500},
        "raw_intensity_matrix": np.round(ocean, 5).tolist(),
        "land_mask_grid": land_mask.tolist()
    }

    with open(OUTPUT_DIR / "sample_sar_scene.json", "w", encoding="utf-8") as f:
        json.dump(sar_data, f, indent=2)
    print("[OK] Generated data/sample/sample_sar_scene.json")

if __name__ == "__main__":
    generate_sar_scene()
