"""
Deterministic Synthetic Data Generator for SlickTrace v2
Generates realistic oil spill observations, AIS vessel tracks, vessel metadata, and metocean fields.
Random seed is fixed at 42 to ensure reproducible, deterministic output.
"""
import json
import math
import numpy as np
from pathlib import Path

# Fix random seed for deterministic generation
np.random.seed(42)

OUTPUT_DIR = Path(__file__).resolve().parent

def generate_spill():
    """Generates synthetic satellite oil spill observation with realistic elongated polygon geometry."""
    center_lat, center_lon = 18.9100, 72.3500
    
    # Construct an elongated slick polygon oriented along 235 degrees (drift axis)
    # Using 12 perimeter vertices with minor noise
    angle_rad = math.radians(235.0)
    major_len = 0.045  # ~5 km along major axis
    minor_len = 0.012  # ~1.3 km along minor axis
    
    polygon = []
    num_points = 14
    for i in range(num_points):
        t = 2 * math.pi * i / num_points
        # Ellipse in local offset
        dx = major_len * math.cos(t)
        dy = minor_len * math.sin(t)
        
        # Rotate by orientation angle
        rx = dx * math.cos(angle_rad) - dy * math.sin(angle_rad)
        ry = dx * math.sin(angle_rad) + dy * math.cos(angle_rad)
        
        # Add deterministic perturbation
        noise_x = (np.sin(i * 3.5) * 0.0015)
        noise_y = (np.cos(i * 2.8) * 0.0012)
        
        lon = round(center_lon + rx + noise_x, 5)
        lat = round(center_lat + ry + noise_y, 5)
        polygon.append([lon, lat])
        
    polygon.append(polygon[0])  # Close ring

    spill_data = {
        "spill_id": "SLICK-IN-2026-009",
        "timestamp": "2026-09-12T14:30:00Z",
        "latitude": center_lat,
        "longitude": center_lon,
        "area_km2": 14.85,
        "perimeter_km": 18.40,
        "length_km": 8.60,
        "orientation_deg": 235.0,
        "confidence": 0.94,
        "polygon": polygon
    }

    with open(OUTPUT_DIR / "spill.json", "w", encoding="utf-8") as f:
        json.dump(spill_data, f, indent=2)
    print("[OK] Generated data/sample/spill.json")

def generate_vessels():
    """Generates metadata for 8 diverse vessels."""
    vessels = [
        {
            "mmsi": 419001234,
            "vessel_name": "MV Ocean Titan",
            "vessel_type": "Oil / Chemical Tanker",
            "length": 245.0,
            "flag": "Panama",
            "operational_capability": "Crude Oil Transport / COW Tank Washing",
            "category": "Prime Candidate (AIS Gap + Speed Drop)"
        },
        {
            "mmsi": 419005678,
            "vessel_name": "MT Pearl Trader",
            "vessel_type": "Chemical Tanker",
            "length": 182.0,
            "flag": "Liberia",
            "operational_capability": "Chemical & Refined Product Carrier",
            "category": "Candidate (Course Alteration)"
        },
        {
            "mmsi": 419003333,
            "vessel_name": "MV Arabian Wave",
            "vessel_type": "Product Tanker",
            "length": 198.0,
            "flag": "Marshall Islands",
            "operational_capability": "Refined Petroleum Fuels",
            "category": "Physically Inconsistent Candidate (Downwind/Upstream Transit)"
        },
        {
            "mmsi": 419007777,
            "vessel_name": "Matsya Kanya 04",
            "vessel_type": "Fishing Vessel",
            "length": 32.0,
            "flag": "India",
            "operational_capability": "Deep Sea Gillnet & Trawling",
            "category": "Irrelevant Fishing Vessel"
        },
        {
            "mmsi": 419009876,
            "vessel_name": "CSCL Star Voyager",
            "vessel_type": "Container Ship",
            "length": 334.0,
            "flag": "Hong Kong",
            "operational_capability": "Containerized Freight",
            "category": "Irrelevant Cargo Vessel"
        },
        {
            "mmsi": 419002222,
            "vessel_name": "INS Taragiri",
            "vessel_type": "Naval Patrol Vessel",
            "length": 126.0,
            "flag": "India",
            "operational_capability": "Coastal Guard / EEZ Surveillance Patrol",
            "category": "Irrelevant Defense Vessel"
        },
        {
            "mmsi": 419004444,
            "vessel_name": "MV Sea Pioneer",
            "vessel_type": "Bulk Carrier",
            "length": 225.0,
            "flag": "Singapore",
            "operational_capability": "Ore & Dry Bulk Transit",
            "category": "Irrelevant Commercial Transit"
        },
        {
            "mmsi": 419008888,
            "vessel_name": "SS Sagar Ratna",
            "vessel_type": "Offshore Supply Tug",
            "length": 65.0,
            "flag": "India",
            "operational_capability": "Anchor Handling / Rig Support",
            "category": "Relevant Support Vessel"
        }
    ]

    with open(OUTPUT_DIR / "vessels.json", "w", encoding="utf-8") as f:
        json.dump(vessels, f, indent=2)
    print("[OK] Generated data/sample/vessels.json")

def generate_ais_tracks():
    """Generates detailed AIS trajectories for all 8 vessels with specific anomaly behaviors."""
    tracks = [
        # Vessel 1: MV Ocean Titan (Prime Suspect - AIS Gap + Speed Drop during spill window)
        {
            "mmsi": 419001234,
            "vessel_name": "MV Ocean Titan",
            "vessel_type": "Oil / Chemical Tanker",
            "has_ais_gap": True,
            "gap_duration_mins": 45,
            "has_course_deviation": False,
            "physical_inconsistency": False,
            "path": [
                {"timestamp": "2026-09-12T00:00:00Z", "latitude": 18.7800, "longitude": 72.1500, "speed_knots": 14.5, "heading_deg": 45.0, "course_deg": 45.0},
                {"timestamp": "2026-09-12T01:30:00Z", "latitude": 18.8200, "longitude": 72.2000, "speed_knots": 14.0, "heading_deg": 45.0, "course_deg": 45.0},
                # AIS Gap Start at 02:15Z near origin zone
                {"timestamp": "2026-09-12T02:15:00Z", "latitude": 18.8420, "longitude": 72.2440, "speed_knots": 2.1, "heading_deg": 50.0, "course_deg": 50.0},
                # Transponder OFF during 02:15Z - 03:00Z
                {"timestamp": "2026-09-12T03:00:00Z", "latitude": 18.8490, "longitude": 72.2520, "speed_knots": 1.8, "heading_deg": 48.0, "course_deg": 48.0},
                {"timestamp": "2026-09-12T04:30:00Z", "latitude": 18.8900, "longitude": 72.3100, "speed_knots": 13.8, "heading_deg": 45.0, "course_deg": 45.0},
                {"timestamp": "2026-09-12T06:00:00Z", "latitude": 18.9400, "longitude": 72.3800, "speed_knots": 14.2, "heading_deg": 45.0, "course_deg": 45.0}
            ]
        },
        # Vessel 2: MT Pearl Trader (Chemical Tanker - Course Deviation near origin)
        {
            "mmsi": 419005678,
            "vessel_name": "MT Pearl Trader",
            "vessel_type": "Chemical Tanker",
            "has_ais_gap": False,
            "gap_duration_mins": 0,
            "has_course_deviation": True,
            "physical_inconsistency": False,
            "path": [
                {"timestamp": "2026-09-12T01:00:00Z", "latitude": 18.8000, "longitude": 72.2800, "speed_knots": 11.2, "heading_deg": 10.0, "course_deg": 10.0},
                {"timestamp": "2026-09-12T02:30:00Z", "latitude": 18.8350, "longitude": 72.2750, "speed_knots": 10.5, "heading_deg": 45.0, "course_deg": 45.0}, # Sharp turn
                {"timestamp": "2026-09-12T03:10:00Z", "latitude": 18.8600, "longitude": 72.2700, "speed_knots": 10.8, "heading_deg": 12.0, "course_deg": 12.0},
                {"timestamp": "2026-09-12T05:00:00Z", "latitude": 18.9200, "longitude": 72.2600, "speed_knots": 11.5, "heading_deg": 10.0, "course_deg": 10.0}
            ]
        },
        # Vessel 3: MV Arabian Wave (Product Tanker - Geographically close but physically inconsistent)
        {
            "mmsi": 419003333,
            "vessel_name": "MV Arabian Wave",
            "vessel_type": "Product Tanker",
            "has_ais_gap": False,
            "gap_duration_mins": 0,
            "has_course_deviation": False,
            "physical_inconsistency": True, # Moving at 16.5 knots SW (225 deg) directly against current vector
            "path": [
                {"timestamp": "2026-09-12T01:30:00Z", "latitude": 18.8800, "longitude": 72.2900, "speed_knots": 16.5, "heading_deg": 225.0, "course_deg": 225.0},
                {"timestamp": "2026-09-12T02:45:00Z", "latitude": 18.8470, "longitude": 72.2510, "speed_knots": 16.2, "heading_deg": 225.0, "course_deg": 225.0}, # 2.1 km from origin
                {"timestamp": "2026-09-12T04:00:00Z", "latitude": 18.8100, "longitude": 72.2100, "speed_knots": 16.8, "heading_deg": 225.0, "course_deg": 225.0}
            ]
        },
        # Vessel 4: Matsya Kanya 04 (Fishing Vessel - Slow erratic fishing trawling)
        {
            "mmsi": 419007777,
            "vessel_name": "Matsya Kanya 04",
            "vessel_type": "Fishing Vessel",
            "has_ais_gap": False,
            "gap_duration_mins": 0,
            "has_course_deviation": True,
            "physical_inconsistency": False,
            "path": [
                {"timestamp": "2026-09-12T01:00:00Z", "latitude": 18.9800, "longitude": 72.4200, "speed_knots": 3.2, "heading_deg": 120.0, "course_deg": 120.0},
                {"timestamp": "2026-09-12T03:00:00Z", "latitude": 18.9600, "longitude": 72.4400, "speed_knots": 2.8, "heading_deg": 280.0, "course_deg": 280.0},
                {"timestamp": "2026-09-12T05:00:00Z", "latitude": 18.9700, "longitude": 72.4100, "speed_knots": 3.5, "heading_deg": 190.0, "course_deg": 190.0}
            ]
        },
        # Vessel 5: CSCL Star Voyager (Container Ship - Commercial shipping lane transit)
        {
            "mmsi": 419009876,
            "vessel_name": "CSCL Star Voyager",
            "vessel_type": "Container Ship",
            "has_ais_gap": False,
            "gap_duration_mins": 0,
            "has_course_deviation": False,
            "physical_inconsistency": False,
            "path": [
                {"timestamp": "2026-09-12T00:30:00Z", "latitude": 18.8100, "longitude": 72.3500, "speed_knots": 18.2, "heading_deg": 350.0, "course_deg": 350.0},
                {"timestamp": "2026-09-12T02:00:00Z", "latitude": 18.8800, "longitude": 72.3400, "speed_knots": 18.0, "heading_deg": 350.0, "course_deg": 350.0},
                {"timestamp": "2026-09-12T03:30:00Z", "latitude": 18.9500, "longitude": 72.3300, "speed_knots": 18.5, "heading_deg": 350.0, "course_deg": 350.0}
            ]
        },
        # Vessel 6: INS Taragiri (Naval Patrol - High speed surveillance transit)
        {
            "mmsi": 419002222,
            "vessel_name": "INS Taragiri",
            "vessel_type": "Naval Patrol Vessel",
            "has_ais_gap": False,
            "gap_duration_mins": 0,
            "has_course_deviation": False,
            "physical_inconsistency": False,
            "path": [
                {"timestamp": "2026-09-12T02:00:00Z", "latitude": 18.9500, "longitude": 72.4000, "speed_knots": 22.0, "heading_deg": 180.0, "course_deg": 180.0},
                {"timestamp": "2026-09-12T04:00:00Z", "latitude": 18.8800, "longitude": 72.4000, "speed_knots": 20.0, "heading_deg": 180.0, "course_deg": 180.0}
            ]
        },
        # Vessel 7: MV Sea Pioneer (Bulk Carrier - Normal deep water transit)
        {
            "mmsi": 419004444,
            "vessel_name": "MV Sea Pioneer",
            "vessel_type": "Bulk Carrier",
            "has_ais_gap": False,
            "gap_duration_mins": 0,
            "has_course_deviation": False,
            "physical_inconsistency": False,
            "path": [
                {"timestamp": "2026-09-12T01:00:00Z", "latitude": 18.7500, "longitude": 72.1000, "speed_knots": 13.8, "heading_deg": 30.0, "course_deg": 30.0},
                {"timestamp": "2026-09-12T03:30:00Z", "latitude": 18.8200, "longitude": 72.1400, "speed_knots": 14.0, "heading_deg": 30.0, "course_deg": 30.0}
            ]
        },
        # Vessel 8: SS Sagar Ratna (Offshore Supply Tug - Offshore rig support)
        {
            "mmsi": 419008888,
            "vessel_name": "SS Sagar Ratna",
            "vessel_type": "Offshore Supply Tug",
            "has_ais_gap": False,
            "gap_duration_mins": 0,
            "has_course_deviation": False,
            "physical_inconsistency": False,
            "path": [
                {"timestamp": "2026-09-12T01:30:00Z", "latitude": 18.8900, "longitude": 72.2200, "speed_knots": 6.2, "heading_deg": 90.0, "course_deg": 90.0},
                {"timestamp": "2026-09-12T03:30:00Z", "latitude": 18.8920, "longitude": 72.2450, "speed_knots": 5.8, "heading_deg": 95.0, "course_deg": 95.0}
            ]
        }
    ]

    with open(OUTPUT_DIR / "ais_tracks.json", "w", encoding="utf-8") as f:
        json.dump(tracks, f, indent=2)
    print("[OK] Generated data/sample/ais_tracks.json")

def generate_metocean():
    """Generates synthetic wind and ocean current field data around the spill region."""
    # Metocean forcing parameters
    metocean_data = {
        "region": "Offshore Mumbai (Arabian Sea)",
        "timestamp": "2026-09-12T14:30:00Z",
        "wind": {
            "speed_knots": 14.2,
            "direction_deg": 210.0,
            "u_ms": 3.65,
            "v_ms": 6.32
        },
        "current": {
            "speed_knots": 1.4,
            "direction_deg": 245.0,
            "u_ms": 0.65,
            "v_ms": 0.30
        },
        "wave_height_m": 1.2,
        "sea_surface_temp_c": 28.5,
        "vector_grid": []
    }

    # Generate a 4x4 spatial vector grid around Mumbai offshore (18.75 to 19.05 N, 72.15 to 72.45 E)
    lats = np.linspace(18.75, 19.05, 4)
    lons = np.linspace(72.15, 72.45, 4)
    
    grid_points = []
    for lat in lats:
        for lon in lons:
            # Add subtle spatial gradients
            wind_speed = round(float(14.2 + (lat - 18.9) * 2.0), 2)
            curr_speed = round(float(1.4 + (lon - 72.3) * 0.5), 2)
            grid_points.append({
                "latitude": round(float(lat), 4),
                "longitude": round(float(lon), 4),
                "wind_speed_knots": wind_speed,
                "wind_direction_deg": 210.0,
                "current_speed_knots": curr_speed,
                "current_direction_deg": 245.0
            })
            
    metocean_data["vector_grid"] = grid_points

    with open(OUTPUT_DIR / "metocean.json", "w", encoding="utf-8") as f:
        json.dump(metocean_data, f, indent=2)
    print("[OK] Generated data/sample/metocean.json")

if __name__ == "__main__":
    generate_spill()
    generate_vessels()
    generate_ais_tracks()
    generate_metocean()
    print("--> All synthetic demo datasets generated deterministically (seed=42).")
