import pandas as pd
import sqlite3
import numpy as np
import datetime

def generate_synthetic_ais_data(db_path: str):
    """
    Generates a synthetic AccessAIS dataset for the prototype.
    """
    conn = sqlite3.connect(db_path)
    
    # Generate some mock data
    np.random.seed(42)
    mmsis = ["257894000", "311000123", "477999888", "111222333", "444555666"]
    names = ["NORDIC TRADER", "OCEAN STAR", "PACIFIC GULL", "FISHING V1", "CARGO V2"]
    types = ["Tanker", "Cargo", "Tanker", "Fishing", "Cargo"]
    
    records = []
    base_time = pd.to_datetime("2026-09-16 07:00:00")
    
    for i in range(5):
        mmsi = mmsis[i]
        name = names[i]
        v_type = types[i]
        
        # Generate 24 hours of data, every 10 mins
        for m in range(0, 24 * 60, 10):
            current_time = base_time + pd.Timedelta(minutes=m)
            
            # Base logic to make NORDIC TRADER pass through our Origin Window (27.850, -89.500 at 09:15)
            if mmsi == "257894000":
                lat = 27.850 + (m - 135) * 0.001
                lon = -89.500 + (m - 135) * 0.001
                sog = 12.0
                
                # Introduce speed drop anomaly
                if 120 < m < 150: # Between 09:00 and 09:30
                    sog = 3.1
                    
                # Introduce AIS gap
                if 150 <= m <= 160: 
                    continue # Skip recording to simulate gap
                    
            else:
                lat = 27.8 + np.random.uniform(-0.5, 0.5)
                lon = -89.5 + np.random.uniform(-0.5, 0.5)
                sog = np.random.uniform(10, 15)
                
            records.append({
                "MMSI": mmsi,
                "VesselName": name,
                "VesselType": v_type,
                "BaseDateTime": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "LAT": lat,
                "LON": lon,
                "SOG": sog,
                "COG": np.random.uniform(0, 360)
            })
            
    df = pd.DataFrame(records)
    df.to_sql("ais_data", conn, if_exists="replace", index=False)
    conn.close()

def query_origin_window(db_path: str, start_time: str, end_time: str, lat: float, lon: float, radius_km: float):
    """
    Queries the database for vessels in the origin window.
    """
    conn = sqlite3.connect(db_path)
    
    # In a real scenario, use spatial indexing (like Spatialite)
    # This is a naive box filter for the prototype
    lat_diff = radius_km / 111.0 # approx degrees
    lon_diff = radius_km / 111.0
    
    query = f"""
    SELECT DISTINCT MMSI, VesselName, VesselType
    FROM ais_data
    WHERE BaseDateTime BETWEEN '{start_time}' AND '{end_time}'
    AND LAT BETWEEN {lat - lat_diff} AND {lat + lat_diff}
    AND LON BETWEEN {lon - lon_diff} AND {lon + lon_diff}
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    return df
