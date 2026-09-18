import pandas as pd
import sqlite3

def calculate_guilt_score(db_path: str, mmsi: str, origin_start: str, origin_end: str):
    """
    Analyzes vessel behavior (SOG, COG, AIS gaps) during the origin window to calculate a Guilt Score.
    """
    conn = sqlite3.connect(db_path)
    
    query = f"""
    SELECT BaseDateTime, SOG, COG
    FROM ais_data
    WHERE MMSI = '{mmsi}'
    ORDER BY BaseDateTime
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    if df.empty:
        return 0, []
        
    df['BaseDateTime'] = pd.to_datetime(df['BaseDateTime'])
    df = df.set_index('BaseDateTime')
    
    score = 50 # Base suspicion for being in the area
    anomalies = []
    
    # Filter for the origin window
    window = df.loc[origin_start:origin_end]
    
    if window.empty:
        # Huge AIS gap exactly during origin window
        score += 40
        anomalies.append("Total AIS blackout during the origin window.")
        return min(score, 100), anomalies
        
    # Check for significant speed drops
    avg_speed_before = df.loc[:origin_start]['SOG'].mean()
    min_speed_window = window['SOG'].min()
    
    if pd.notna(avg_speed_before) and pd.notna(min_speed_window):
        if min_speed_window < (avg_speed_before * 0.4): # Dropped by more than 60%
            score += 30
            anomalies.append(f"Significant speed drop detected (from avg {avg_speed_before:.1f} to {min_speed_window:.1f} knots).")
            
    # Check for AIS transmission gaps in the window (assuming standard is every few minutes, if gap > 15 mins)
    time_diffs = window.index.to_series().diff().dt.total_seconds() / 60
    max_gap = time_diffs.max()
    
    if pd.notna(max_gap) and max_gap > 15:
        score += 20
        anomalies.append(f"AIS transmission gap of {max_gap:.0f} minutes detected.")
        
    return min(score, 100), anomalies
