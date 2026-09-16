from typing import List, Tuple
from backend.services.ais.schemas import AisTrack, AisPoint
from backend.services.anomaly.schemas import AnomalyExplainability
from backend.services.ais.cleaning import parse_time
import math

def detect_speed_reduction(track: AisTrack) -> AnomalyExplainability:
    """
    Detects sudden drops in speed that might indicate an illicit ship-to-ship transfer,
    discharge, or other anomalous behavior.
    """
    if len(track.points) < 2:
        return AnomalyExplainability(detected=False, classification="normal", reason="Not enough data points", severity=0.0)
        
    max_drop = 0.0
    detected_drop_pt = None
    
    for i in range(1, len(track.points)):
        pt1 = track.points[i-1]
        pt2 = track.points[i]
        
        speed_drop = pt1.speed_knots - pt2.speed_knots
        if speed_drop > max_drop:
            max_drop = speed_drop
            detected_drop_pt = pt2
            
    # Assuming standard cruise > 10kts, drop to < 3kts is highly suspicious
    if max_drop >= 8.0 and detected_drop_pt and detected_drop_pt.speed_knots <= 3.0:
        return AnomalyExplainability(
            detected=True,
            classification="suspicious",
            reason=f"Sudden speed drop of {max_drop:.1f} knots down to {detected_drop_pt.speed_knots:.1f} knots",
            severity=min(1.0, max_drop / 15.0)
        )
        
    return AnomalyExplainability(
        detected=False,
        classification="normal",
        reason="Speed profile is consistent with normal transit",
        severity=0.0
    )

def detect_course_deviation(track: AisTrack) -> AnomalyExplainability:
    """
    Detects erratic maneuvering, U-turns, or large course deviations.
    """
    if len(track.points) < 3:
        return AnomalyExplainability(detected=False, classification="normal", reason="Not enough data points", severity=0.0)
        
    max_dev = 0.0
    
    for i in range(1, len(track.points)):
        pt1 = track.points[i-1]
        pt2 = track.points[i]
        
        # Calculate angular difference (handling 360 wrap-around)
        diff = abs(pt1.heading_deg - pt2.heading_deg)
        dev = min(diff, 360 - diff)
        
        if dev > max_dev:
            max_dev = dev
            
    if max_dev > 45.0:
        return AnomalyExplainability(
            detected=True,
            classification="suspicious",
            reason=f"Significant course deviation of {max_dev:.1f} degrees detected",
            severity=min(1.0, max_dev / 180.0)
        )
        
    return AnomalyExplainability(
        detected=False,
        classification="normal",
        reason="Heading profile is consistent with normal transit",
        severity=0.0
    )

def detect_unusual_stopping(track: AisTrack) -> AnomalyExplainability:
    """
    Detects vessels that stop (speed ~ 0) for extended periods in open waters.
    """
    if not track.points:
        return AnomalyExplainability(detected=False, classification="normal", reason="No data", severity=0.0)
        
    stop_duration_hours = 0.0
    is_stopped = False
    stop_start = None
    
    for pt in track.points:
        if pt.speed_knots < 0.5:
            if not is_stopped:
                is_stopped = True
                stop_start = parse_time(pt.timestamp)
            else:
                current_time = parse_time(pt.timestamp)
                stop_duration_hours = (current_time - stop_start).total_seconds() / 3600.0
        else:
            is_stopped = False
            
    if stop_duration_hours > 2.0:
        return AnomalyExplainability(
            detected=True,
            classification="suspicious",
            reason=f"Unusual stop lasting {stop_duration_hours:.1f} hours detected",
            duration_minutes=stop_duration_hours * 60,
            severity=min(1.0, stop_duration_hours / 12.0)
        )
        
    return AnomalyExplainability(
        detected=False,
        classification="normal",
        reason="No unusual extended stops detected",
        severity=0.0
    )
