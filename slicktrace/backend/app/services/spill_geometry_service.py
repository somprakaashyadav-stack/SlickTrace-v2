"""
SlickTrace v2 — Geospatial Spill Geometry Generation Engine

Implements:
1. Morphological cleanup (closing, opening, hole-filling)
2. Connected component labeling & noise filtering
3. Vector polygonization (Rasterio features.shapes / OpenCV)
4. Geometry simplification (Douglas-Peucker, topology-preserving)
5. Validity repair (make_valid / buffer(0))
6. Metric area (km2) & perimeter (km) calculation in Projected UTM CRS (not raw degrees)
7. Centroid & Bounding Box extraction in WGS84
8. Geometry quality diagnostics
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from scipy.ndimage import binary_closing, binary_opening, binary_fill_holes
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    import rasterio
    from rasterio import features
    from rasterio.transform import Affine
    from rasterio.crs import CRS
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False

try:
    from shapely.geometry import Polygon, MultiPolygon, shape, mapping, box
    from shapely.validation import make_valid
    from shapely.ops import transform as shapely_transform
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False

try:
    from pyproj import Transformer
    PYPROJ_AVAILABLE = True
except ImportError:
    PYPROJ_AVAILABLE = False


def determine_utm_crs(lon: float, lat: float) -> Tuple[int, str]:
    """
    Determines the appropriate Universal Transverse Mercator (UTM) EPSG code
    for geodesically accurate metric area and perimeter calculation.

    Returns: (epsg_code, descriptive_name)
    """
    # Wrap longitude to -180..180
    norm_lon = ((lon + 180.0) % 360.0) - 180.0
    zone = int(math.floor((norm_lon + 180.0) / 6.0)) + 1
    zone = min(max(zone, 1), 60)

    is_north = lat >= 0.0
    epsg = 32600 + zone if is_north else 32700 + zone
    hemisphere = "N" if is_north else "S"
    desc = f"EPSG:{epsg} (WGS 84 / UTM zone {zone}{hemisphere})"
    return epsg, desc


def clean_binary_mask(
    mask: np.ndarray,
    close_kernel_size: int = 5,
    open_kernel_size: int = 3,
    min_component_pixels: int = 15,
) -> np.ndarray:
    """
    Performs morphological cleanup on raw segmentation probability masks:
    - Binary closing: fills pinholes and micro-cracks inside slick bodies.
    - Binary opening: removes isolated single-pixel false alarms.
    - Small connected component noise removal.
    """
    binary = (mask > 0).astype(np.uint8)

    if CV2_AVAILABLE:
        # Morphological Closing
        close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_kernel_size, close_kernel_size))
        closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, close_kernel)

        # Fill holes
        contours, hierarchy = cv2.findContours(closed, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        filled = np.zeros_like(closed)
        for i, c in enumerate(contours):
            cv2.drawContours(filled, [c], -1, 1, thickness=cv2.FILLED)

        # Morphological Opening
        open_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (open_kernel_size, open_kernel_size))
        cleaned = cv2.morphologyEx(filled, cv2.MORPH_OPEN, open_kernel)

        # Filter small noise components
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(cleaned)
        final_mask = np.zeros_like(cleaned)
        for i in range(1, num_labels):
            if stats[i, cv2.CC_STAT_AREA] >= min_component_pixels:
                final_mask[labels == i] = 1
        return final_mask

    elif SCIPY_AVAILABLE:
        closed = binary_closing(binary, structure=np.ones((close_kernel_size, close_kernel_size)))
        filled = binary_fill_holes(closed)
        cleaned = binary_opening(filled, structure=np.ones((open_kernel_size, open_kernel_size)))
        return cleaned.astype(np.uint8)

    return binary


class SpillGeometryEngine:
    """
    Engine for vector polygonization, topology repair, metric calculations, and simplification.
    """

    @classmethod
    def generate_spill_geometry(
        cls,
        mask: np.ndarray,
        transform: Optional[Any] = None,
        source_crs: Optional[Any] = None,
        simplification_tolerance: float = 0.0001,  # ~10m in WGS84 degrees
        pixel_size_m: float = 10.0,
    ) -> Dict[str, Any]:
        """
        Executes full pipeline:
        mask → cleanup → polygonization → repair → simplification → projected UTM metric area/perimeter.
        """
        # 1. Morphological Cleanup
        cleaned = clean_binary_mask(mask)
        total_pixels = int(np.sum(cleaned))

        if total_pixels == 0:
            return {
                "geojson_polygon": None,
                "area_km2": 0.0,
                "perimeter_km": 0.0,
                "projected_crs": "None",
                "centroid_lat": 0.0,
                "centroid_lon": 0.0,
                "bbox": [0.0, 0.0, 0.0, 0.0],
                "geometry_quality": {
                    "validity": "empty",
                    "vertex_count": 0,
                    "components_count": 0,
                    "simplification_tolerance": simplification_tolerance,
                },
            }

        # 2. Vector Polygonization & Geometry
        if not SHAPELY_AVAILABLE:
            # Pure-Python fallback when GEOS/Shapely C-extension is not installed
            rows, cols = np.where(cleaned > 0)
            min_col, max_col = float(np.min(cols)), float(np.max(cols))
            min_row, max_row = float(np.min(rows)), float(np.max(rows))
            mean_col = float(np.mean(cols))
            mean_row = float(np.mean(rows))

            if transform is not None:
                # Affine projection: x = c + a*col + b*row, y = f + d*col + e*row
                x0, y0 = transform * (min_col, min_row)
                x1, y1 = transform * (max_col, max_row)
                c_lon, c_lat = transform * (mean_col, mean_row)
                min_x, max_x = min(x0, x1), max(x0, x1)
                min_y, max_y = min(y0, y1), max(y0, y1)
                utm_epsg, utm_name = determine_utm_crs(c_lon, c_lat)
                lat_rad = math.radians(c_lat)
                m_per_deg_lat = 111132.92 - 559.82 * math.cos(2 * lat_rad)
                m_per_deg_lon = 111412.84 * math.cos(lat_rad)
                # Area of active pixels * pixel dimension in meters
                deg_w = abs(max_x - min_x) / max(1, (max_col - min_col))
                deg_h = abs(max_y - min_y) / max(1, (max_row - min_row))
                px_area_m2 = (deg_w * m_per_deg_lon) * (deg_h * m_per_deg_lat)
                metric_area_m2 = total_pixels * px_area_m2
                metric_perimeter_m = 2 * ((max_col - min_col) * deg_w * m_per_deg_lon + (max_row - min_row) * deg_h * m_per_deg_lat)
            else:
                min_x, max_x = min_col, max_col
                min_y, max_y = min_row, max_row
                c_lon, c_lat = mean_col, mean_row
                utm_name = f"Pixel Space ({pixel_size_m}m ground resolution)"
                metric_area_m2 = float(total_pixels * (pixel_size_m ** 2))
                metric_perimeter_m = float(2 * ((max_col - min_col) + (max_row - min_row)) * pixel_size_m)

            geojson_poly = {
                "type": "Polygon",
                "coordinates": [[
                    [min_x, min_y],
                    [max_x, min_y],
                    [max_x, max_y],
                    [min_x, max_y],
                    [min_x, min_y],
                ]],
            }

            return {
                "geojson_polygon": geojson_poly,
                "area_km2": round(metric_area_m2 / 1e6, 4),
                "perimeter_km": round(metric_perimeter_m / 1e3, 3),
                "projected_crs": utm_name,
                "centroid_lat": round(c_lat, 6),
                "centroid_lon": round(c_lon, 6),
                "bbox": [round(min_x, 6), round(min_y, 6), round(max_x, 6), round(max_y, 6)],
                "geometry_quality": {
                    "validity": "valid",
                    "simplification_tolerance": simplification_tolerance,
                    "vertex_count": 5,
                    "components_count": 1,
                    "projected_crs_used": utm_name,
                    "pixel_fill_count": total_pixels,
                },
            }

        polygons: List[Polygon] = []

        if RASTERIO_AVAILABLE and transform is not None:
            # Vectorize with affine georeferencing
            shapes_gen = features.shapes(
                cleaned.astype(np.int16),
                mask=(cleaned > 0),
                transform=transform,
            )
            for geom_dict, val in shapes_gen:
                if val == 1:
                    poly = shape(geom_dict)
                    if not poly.is_empty:
                        polygons.append(poly)
        else:
            # Pixel-space contouring fallback
            if CV2_AVAILABLE:
                contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for cnt in contours:
                    if len(cnt) >= 3:
                        pts = cnt.squeeze(axis=1)
                        # Close polygon ring
                        pts = np.vstack([pts, pts[0]])
                        if transform is not None:
                            trans_pts = [transform * (float(pt[0]), float(pt[1])) for pt in pts]
                            polygons.append(Polygon(trans_pts))
                        else:
                            polygons.append(Polygon(pts))
            else:
                # Bounding box fallback with Shapely box
                rows, cols = np.where(cleaned > 0)
                if transform is not None:
                    x0, y0 = transform * (float(np.min(cols)), float(np.min(rows)))
                    x1, y1 = transform * (float(np.max(cols)), float(np.max(rows)))
                    polygons.append(box(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)))
                else:
                    polygons.append(box(float(np.min(cols)), float(np.min(rows)), float(np.max(cols)), float(np.max(rows))))

        if not polygons:
            return {
                "geojson_polygon": None,
                "area_km2": 0.0,
                "perimeter_km": 0.0,
                "projected_crs": "None",
                "centroid_lat": 0.0,
                "centroid_lon": 0.0,
                "bbox": [0.0, 0.0, 0.0, 0.0],
                "geometry_quality": {"validity": "empty"},
            }

        # Combine into MultiPolygon
        if len(polygons) == 1:
            raw_geom = polygons[0]
        else:
            from shapely.ops import unary_union
            raw_geom = unary_union(polygons)

        # 3. Validity Repair
        validity_status = "valid"
        if not raw_geom.is_valid:
            validity_status = "repaired"
            try:
                raw_geom = make_valid(raw_geom)
            except Exception:
                raw_geom = raw_geom.buffer(0)

        # Ensure we only have 2D Polygon or MultiPolygon (strip any points/lines from repair)
        if raw_geom.geom_type not in ("Polygon", "MultiPolygon"):
            sub_polys = [g for g in getattr(raw_geom, "geoms", []) if g.geom_type in ("Polygon", "MultiPolygon")]
            if sub_polys:
                from shapely.ops import unary_union
                raw_geom = unary_union(sub_polys)
            else:
                raw_geom = raw_geom.convex_hull

        # 4. Douglas-Peucker Geometry Simplification
        simplified_geom = raw_geom.simplify(simplification_tolerance, preserve_topology=True)
        if not simplified_geom.is_valid:
            simplified_geom = make_valid(simplified_geom)

        # 5. Extract Centroid & Bounding Box in WGS84
        c = simplified_geom.centroid
        centroid_lon = float(c.x)
        centroid_lat = float(c.y)

        min_x, min_y, max_x, max_y = simplified_geom.bounds
        bbox = [round(float(min_x), 6), round(float(min_y), 6), round(float(max_x), 6), round(float(max_y), 6)]

        # 6. Projected Metric Area & Perimeter Calculation
        # CRITICAL CONTRACT: Calculate area in an appropriate projected CRS, not raw degrees!
        if transform is not None:
            utm_epsg, utm_name = determine_utm_crs(centroid_lon, centroid_lat)
            if PYPROJ_AVAILABLE:
                transformer = Transformer.from_crs("EPSG:4326", f"EPSG:{utm_epsg}", always_xy=True)
                projected_geom = shapely_transform(transformer.transform, simplified_geom)
                metric_area_m2 = float(projected_geom.area)
                metric_perimeter_m = float(projected_geom.length)
            else:
                # Geodesic spherical approximation fallback if pyproj absent
                lat_rad = math.radians(centroid_lat)
                m_per_deg_lat = 111132.92 - 559.82 * math.cos(2 * lat_rad)
                m_per_deg_lon = 111412.84 * math.cos(lat_rad)
                metric_area_m2 = float(simplified_geom.area * m_per_deg_lat * m_per_deg_lon)
                metric_perimeter_m = float(simplified_geom.length * (m_per_deg_lat + m_per_deg_lon) / 2.0)
        else:
            # Ungeoreferenced pixel space -> metric conversion via pixel_size_m
            utm_name = f"Pixel Space ({pixel_size_m}m ground resolution)"
            metric_area_m2 = float(total_pixels * (pixel_size_m ** 2))
            metric_perimeter_m = float(simplified_geom.length * pixel_size_m)

        area_km2 = round(metric_area_m2 / 1e6, 4)
        perimeter_km = round(metric_perimeter_m / 1e3, 3)

        # 7. Quality Metrics
        vertex_count = 0
        if simplified_geom.geom_type == "Polygon":
            vertex_count = len(simplified_geom.exterior.coords)
        elif simplified_geom.geom_type == "MultiPolygon":
            vertex_count = sum(len(p.exterior.coords) for p in simplified_geom.geoms)

        components_count = len(simplified_geom.geoms) if hasattr(simplified_geom, "geoms") else 1

        quality = {
            "validity": validity_status,
            "simplification_tolerance": simplification_tolerance,
            "vertex_count": vertex_count,
            "components_count": components_count,
            "projected_crs_used": utm_name,
            "pixel_fill_count": total_pixels,
        }

        geojson_out = mapping(simplified_geom)

        return {
            "geojson_polygon": geojson_out,
            "area_km2": area_km2,
            "perimeter_km": perimeter_km,
            "projected_crs": utm_name,
            "centroid_lat": round(centroid_lat, 6),
            "centroid_lon": round(centroid_lon, 6),
            "bbox": bbox,
            "geometry_quality": quality,
        }
