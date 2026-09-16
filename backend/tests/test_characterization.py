import pytest
from backend.services.characterization.geometry import (
    haversine_distance,
    calculate_centroid,
    calculate_bounding_box,
    calculate_length_width_orientation,
    calculate_fragmentation,
    characterize_slick
)

def test_haversine_distance():
    # Known distance approx: 1 degree latitude is ~111 km
    dist = haversine_distance(0, 0, 0, 1)
    assert 110 < dist < 112

def test_calculate_centroid():
    # Simple square polygon
    poly = [[0.0, 0.0], [0.0, 2.0], [2.0, 2.0], [2.0, 0.0], [0.0, 0.0]]
    centroid = calculate_centroid(poly)
    assert centroid == [1.0, 1.0]

def test_calculate_bounding_box():
    poly = [[0.0, 1.0], [2.0, 3.0], [-1.0, 2.0], [0.0, 1.0]]
    bbox = calculate_bounding_box(poly)
    assert bbox == [[-1.0, 1.0], [2.0, 3.0]]

def test_calculate_length_width_orientation():
    # Very small polygon, roughly 1 degree long vertically
    poly = [[0.0, 0.0], [0.0, 1.0], [0.1, 1.0], [0.1, 0.0], [0.0, 0.0]]
    # area_km2 roughly 111 * 11.1 = 1232 km2
    length, width, orientation = calculate_length_width_orientation(poly, 1232.0)
    
    assert length > 110
    assert width > 0
    # The major axis points from (0,0) to (0.1, 1.0) roughly, dlon=0.1, dlat=1.0 -> 5.71 deg
    assert 5.0 < orientation < 6.0


def test_calculate_fragmentation():
    # Perfect circle fragmentation is 1.0
    # Area = 100, Perimeter of circle = 2*sqrt(pi*100) = ~35.449
    frag = calculate_fragmentation(35.449, 100.0)
    assert 0.99 < frag < 1.01
    
    # Highly fragmented is > 1
    frag_high = calculate_fragmentation(70.0, 100.0)
    assert frag_high > 1.9

def test_characterize_slick():
    poly = [[72.0, 18.0], [72.1, 18.1], [72.0, 18.2], [71.9, 18.1], [72.0, 18.0]]
    area = 50.0
    peri = 30.0
    
    stats = characterize_slick(poly, area, peri)
    assert "centroid" in stats
    assert "bounding_box" in stats
    assert "length_km" in stats
    assert "width_km" in stats
    assert "orientation_deg" in stats
    assert "elongation_ratio" in stats
    assert "fragmentation_index" in stats
    
    assert len(stats["centroid"]) == 2
