import math
import numpy as np
from typing import List, Tuple, Dict, Any

def haversine_distance(lon1, lat1, lon2, lat2):
    """Calculate the great circle distance in kilometers between two points on the earth."""
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371 # Radius of earth in kilometers
    return c * r

def calculate_centroid(polygon: List[List[float]]) -> List[float]:
    """Calculate the centroid of a polygon [lon, lat]."""
    pts = polygon[:-1] if polygon[0] == polygon[-1] else polygon
    pts_array = np.array(pts)
    centroid = np.mean(pts_array, axis=0)
    return [round(float(centroid[0]), 5), round(float(centroid[1]), 5)]

def calculate_bounding_box(polygon: List[List[float]]) -> List[List[float]]:
    """Calculate the bounding box of a polygon [[min_lon, min_lat], [max_lon, max_lat]]."""
    pts_array = np.array(polygon)
    min_lon, min_lat = np.min(pts_array, axis=0)
    max_lon, max_lat = np.max(pts_array, axis=0)
    return [[round(float(min_lon), 5), round(float(min_lat), 5)], [round(float(max_lon), 5), round(float(max_lat), 5)]]

def calculate_length_width_orientation(polygon: List[List[float]], area_km2: float) -> Tuple[float, float, float]:
    """
    Calculate the length, width, and orientation of the polygon.
    Returns (length_km, width_km, orientation_deg).
    """
    pts = polygon[:-1] if polygon[0] == polygon[-1] else polygon
    max_dist = 0
    p1_max = pts[0]
    p2_max = pts[1]

    # Find the two furthest points to define the major axis (length)
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            dist = haversine_distance(pts[i][0], pts[i][1], pts[j][0], pts[j][1])
            if dist > max_dist:
                max_dist = dist
                p1_max = pts[i]
                p2_max = pts[j]
    
    length_km = max(max_dist, 0.001)  # Avoid division by zero
    width_km = area_km2 / length_km

    # Calculate orientation based on the major axis
    dlon = p2_max[0] - p1_max[0]
    dlat = p2_max[1] - p1_max[1]
    
    # Simple Cartesian angle approximation for orientation (0 is North, 90 is East)
    # math.atan2(y, x) is math.atan2(dlat, dlon). Standard bearing is math.atan2(dlon, dlat)
    angle_rad = math.atan2(dlon, dlat)
    angle_deg = math.degrees(angle_rad)
    if angle_deg < 0:
        angle_deg += 360

    return round(length_km, 2), round(width_km, 2), round(angle_deg, 2)

def calculate_fragmentation(perimeter_km: float, area_km2: float) -> float:
    """Calculate a fragmentation index (1 = perfect circle, >1 = more fragmented)."""
    if area_km2 <= 0:
        return 1.0
    circle_perimeter = 2 * math.sqrt(math.pi * area_km2)
    frag_index = perimeter_km / circle_perimeter
    return round(frag_index, 2)

def characterize_slick(polygon: List[List[float]], area_km2: float, perimeter_km: float) -> Dict[str, Any]:
    centroid = calculate_centroid(polygon)
    bbox = calculate_bounding_box(polygon)
    length, width, orientation = calculate_length_width_orientation(polygon, area_km2)
    elongation = round(length / max(width, 0.001), 2)
    fragmentation = calculate_fragmentation(perimeter_km, area_km2)

    return {
        "centroid": centroid,
        "bounding_box": bbox,
        "length_km": length,
        "width_km": width,
        "orientation_deg": orientation,
        "elongation_ratio": elongation,
        "fragmentation_index": fragmentation
    }
