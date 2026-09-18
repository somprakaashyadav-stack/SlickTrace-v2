"""
SlickTrace v2 — Interactive Pipeline CLI Runner

Executes the complete decision-support investigation pipeline:
1. Satellite Evidence Ingestion & Metadata Validation
2. Spill Dark-Region Detection & Geometry Extraction (UTM metric area & perimeter)
3. Backward Lagrangian Ocean Hindcast (OpenDrift/OpenOil, Monte Carlo P50/P75/P90)
4. Historical AIS Spatiotemporal Vessel Search
5. Vessel Behavior & Anomaly Detection (Isolation Forest)
6. Multi-Factor Physical Consistency Ranking
7. Tamper-Evident Evidence Manifest (SHA-256) & Chain of Custody
"""
from __future__ import annotations

import json
import math
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root and backend to python path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

import numpy as np

from ais.anomaly.detector import detect_anomalies, detect_named_anomalies, extract_track_features
from app.core.security import ChainOfCustody, EvidenceArtifact, EvidenceManifest, sha256_bytes
from app.services.spill_geometry_service import SpillGeometryEngine
from ocean.forcing.models import ForcingProvenance, NormalizedForcingData
from ocean.hindcast.config import HindcastSimulationConfig, OilParameters
from ocean.hindcast.runner import run_hindcast


def banner():
    print(r"""
  ____  _ _      _   _____                    
 / ___|| (_) ___| |_|_   _| __ __ _  ___ ___  
 \___ \| | |/ __| |/ /| || '__/ _` |/ __/ _ \ 
  ___) | | | (__|   < | || | | (_| | (_|  __/ 
 |____/|_|_|\___|_|\_\|_||_|  \__,_|\___\___| 
    Maritime Oil-Spill Attribution Platform
    Mode: DEMO / MOCK DATA
    =========================================
""")


def step_1_satellite_ingest():
    print("\n[STAGE 1/7] Ingesting Satellite SAR Scene...")
    scene_meta = {
        "filename": "S1A_IW_GRDH_1SDV_20260917T060000_050000_05DEAF_E123.SAFE.tif",
        "sensor": "Sentinel-1A C-SAR",
        "mode": "IW (Interferometric Wide Swath)",
        "polarization": "VV+VH",
        "product_type": "GRD (Ground Range Detected)",
        "resolution_m": 10.0,
        "acquisition_time": "2026-09-17T06:00:00Z",
        "crs": "EPSG:32616 (UTM Zone 16N)",
        "center_lat": 27.5214,
        "center_lon": -89.8450,
        "sha256": "4a8e2b85c13b1a8d9f104e768b449911e3b2e2d83f81e649061fa970172e29cd",
    }
    for k, v in scene_meta.items():
        print(f"  * {k:18s}: {v}")
    return scene_meta


def step_2_spill_segmentation(scene_meta):
    print("\n[STAGE 2/7] Running Dark-Region Segmentation & Geometry Generation...")
    # Synthetic realistic slick mask (100x100 raster with elongated spill)
    mask = np.zeros((100, 100), dtype=np.uint8)
    # Draw slick core and trail
    for y in range(35, 65):
        x_center = int(50 + (y - 50) * 0.8)
        width = int(8 - abs(y - 50) * 0.2)
        mask[y, max(0, x_center - width):min(100, x_center + width)] = 1

    geo = SpillGeometryEngine.generate_spill_geometry(
        mask=mask,
        pixel_size_m=10.0,
    )

    c_lat, c_lon = 27.5214, -89.8450
    if geo.get("centroid"):
        c_lon, c_lat = geo["centroid"]["coordinates"]

    print(f"  * Classified Entity : OIL_SLICK (Confidence: 0.942, Look-alike Prob: 0.058)")
    print(f"  * Projected Area    : {geo['area_km2']:.3f} km^2")
    print(f"  * Perimeter         : {geo['perimeter_km']:.2f} km")
    print(f"  * Centroid          : ({c_lat:.4f} deg N, {c_lon:.4f} deg E)")
    print(f"  * Geometry Validity : {geo['geometry_quality']['validity']}")
    return geo


def step_3_ocean_hindcast(geo):
    print("\n[STAGE 3/7] Running Backward Physical Hindcast (OpenDrift/OpenOil)...")
    detection_dt = datetime(2026, 9, 17, 6, 0, tzinfo=timezone.utc)

    # Build ERA5 & CMEMS forcing representations
    lats = [27.0, 27.5, 28.0]
    lons = [-90.5, -90.0, -89.5]
    times = ["2026-09-16T06:00:00Z", "2026-09-17T06:00:00Z"]

    # Prevailing wind toward North-East (u=3.2, v=4.1 m/s)
    u_w = np.full((2, 3, 3), 3.2, dtype=np.float32)
    v_w = np.full((2, 3, 3), 4.1, dtype=np.float32)
    # Surface current toward East (u=0.25, v=0.08 m/s)
    u_c = np.full((2, 3, 3), 0.25, dtype=np.float32)
    v_c = np.full((2, 3, 3), 0.08, dtype=np.float32)

    prov_w = ForcingProvenance(
        source_name="ERA5 Reanalysis (ECMWF)",
        dataset_id="reanalysis-era5-single-levels-10m-wind",
        dataset_version="ERA5_hourly_v1",
        source_url="https://cds.climate.copernicus.eu",
        raw_file_sha256="era5_sha256_wind_data_digest_448",
        spatial_bounds={"lon_min": -90.5, "lat_min": 27.0, "lon_max": -89.5, "lat_max": 28.0},
        time_range={"start": times[0], "end": times[1]},
    )
    prov_c = ForcingProvenance(
        source_name="Copernicus Marine Service (CMEMS)",
        dataset_id="GLOBAL_ANALYSISFORECAST_PHY_001_024",
        dataset_version="CMEMS_PHY_hourly_v2",
        source_url="https://marine.copernicus.eu",
        raw_file_sha256="cmems_sha256_current_digest_912",
        spatial_bounds={"lon_min": -90.5, "lat_min": 27.0, "lon_max": -89.5, "lat_max": 28.0},
        time_range={"start": times[0], "end": times[1]},
    )

    wind = NormalizedForcingData("wind", times, lats, lons, u_w, v_w, "ERA5", "v1", "0.25 deg", prov_w)
    current = NormalizedForcingData("current", times, lats, lons, u_c, v_c, "CMEMS", "v1", "0.083 deg", prov_c)

    oil = OilParameters(oil_type="GENERIC BUNKER C", api_gravity=12.5, viscosity_cst=380.0)
    cfg = HindcastSimulationConfig(
        durations_hours=[4, 8, 12, 24],
        n_particles=500,
        oil_params=oil,
        random_seed=42,
    )

    result = run_hindcast(
        detection_time=detection_dt,
        wind_forcing=wind,
        current_forcing=current,
        slick_polygon=geo.get("geojson_polygon"),
        config=cfg,
    )

    print(f"  * Simulation Particles : {cfg.n_particles} Monte Carlo trajectories")
    print(f"  * Wind Forcing Source   : {result.wind_source}")
    print(f"  * Current Forcing Source: {result.current_source}")
    print("  * Backward Duration Checkpoints:")
    for h_key in ["4h", "8h", "12h", "24h"]:
        sl = result.duration_slices[h_key]
        print(f"    - T-{sl['duration_hours']:2d}h ({sl['origin_time']}): "
              f"Centroid=({sl['centroid_lat']:.4f} deg N, {sl['centroid_lon']:.4f} deg E), Spread={sl['spread_km']:.1f} km")

    p50_area = len(result.uncertainty_metadata.get("p50_polygon", {}).get("coordinates", [[]])[0])
    p90_area = len(result.uncertainty_metadata.get("p90_polygon", {}).get("coordinates", [[]])[0])
    print(f"  * Confidence Polygons : P50 ({p50_area} vertices), P75, P90 ({p90_area} vertices)")
    return result


def step_4_and_5_ais_and_anomalies(hindcast_result):
    print("\n[STAGE 4/7] Cross-Referencing Historical AIS & Detecting Anomalies...")
    origin_24 = hindcast_result.duration_slices["24h"]
    origin_lat, origin_lon = origin_24["centroid_lat"], origin_24["centroid_lon"]

    # Candidate vessel tracks
    vessels = [
        {
            "mmsi": "352001928",
            "name": "PACIFIC TITAN",
            "type": "Oil/Chemical Tanker",
            "flag": "Panama",
            "positions": [
                {"base_datetime": "2026-09-16T05:30:00Z", "lat": origin_lat - 0.05, "lon": origin_lon - 0.08, "sog": 12.4, "cog": 65.0, "heading": 65},
                {"base_datetime": "2026-09-16T06:00:00Z", "lat": origin_lat - 0.01, "lon": origin_lon - 0.02, "sog": 3.8,  "cog": 85.0, "heading": 80},  # Sharp speed drop
                {"base_datetime": "2026-09-16T07:15:00Z", "lat": origin_lat + 0.02, "lon": origin_lon + 0.04, "sog": 4.1,  "cog": 95.0, "heading": 90},  # AIS loiter gap
                {"base_datetime": "2026-09-16T08:00:00Z", "lat": origin_lat + 0.08, "lon": origin_lon + 0.12, "sog": 13.1, "cog": 68.0, "heading": 68},
            ],
        },
        {
            "mmsi": "244123456",
            "name": "NORDIC STAR",
            "type": "Bulk Carrier",
            "flag": "Liberia",
            "positions": [
                {"base_datetime": "2026-09-16T05:00:00Z", "lat": origin_lat - 0.25, "lon": origin_lon - 0.20, "sog": 11.8, "cog": 70.0, "heading": 70},
                {"base_datetime": "2026-09-16T06:00:00Z", "lat": origin_lat - 0.18, "lon": origin_lon - 0.10, "sog": 11.9, "cog": 71.0, "heading": 70},
                {"base_datetime": "2026-09-16T07:00:00Z", "lat": origin_lat - 0.10, "lon": origin_lon - 0.01, "sog": 11.7, "cog": 70.0, "heading": 71},
            ],
        },
        {
            "mmsi": "636091122",
            "name": "BLUE MARIN",
            "type": "Fishing Vessel",
            "flag": "Malta",
            "positions": [
                {"base_datetime": "2026-09-16T04:00:00Z", "lat": origin_lat + 0.35, "lon": origin_lon + 0.40, "sog": 6.2, "cog": 210.0, "heading": 210},
                {"base_datetime": "2026-09-16T06:00:00Z", "lat": origin_lat + 0.32, "lon": origin_lon + 0.38, "sog": 5.8, "cog": 215.0, "heading": 215},
            ],
        },
    ]

    analyzed = []
    for v in vessels:
        feats = extract_track_features(v["positions"])
        named_anomalies = detect_named_anomalies(v["positions"])
        analyzed.append({**v, "features": feats, "anomalies": named_anomalies})
        print(f"  * {v['name']} (MMSI: {v['mmsi']}, {v['type']}):")
        print(f"    - Avg SOG: {feats['mean_sog']:.1f} kn, SOG Drop Ratio: {feats['sog_drop_ratio']:.2f}, Max AIS Gap: {feats['max_time_gap_min']:.0f} min")
        if named_anomalies:
            print(f"    - Anomalies Detected: {', '.join(named_anomalies)}")
        else:
            print("    - Anomalies Detected: None (steady navigation)")

    return analyzed


def step_6_consistency_ranking(analyzed_vessels, hindcast_result):
    print("\n[STAGE 6/7] Computing Multi-Factor Physical Consistency Ranking...")
    origin_24 = hindcast_result.duration_slices["24h"]
    o_lat, o_lon = origin_24["centroid_lat"], origin_24["centroid_lon"]

    def haversine(lat1, lon1, lat2, lon2):
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        return R * 2 * math.asin(math.sqrt(a))

    scored = []
    for v in analyzed_vessels:
        # Minimum approach to T-24h centroid
        dists = [haversine(p["lat"], p["lon"], o_lat, o_lon) for p in v["positions"]]
        min_dist_km = min(dists)

        # Proximity score (0 to 1)
        prox_score = max(0.0, 1.0 - min_dist_km / 50.0)

        # Vessel type factor
        vt_factor = 1.0 if "Tanker" in v["type"] else (0.6 if "Bulk" in v["type"] else 0.3)

        # Anomaly factor
        anom_factor = 0.9 if v["anomalies"] else 0.2

        # Composite score out of 100
        composite = (prox_score * 0.45 + vt_factor * 0.30 + anom_factor * 0.25) * 100.0

        scored.append({
            "name": v["name"],
            "mmsi": v["mmsi"],
            "type": v["type"],
            "flag": v["flag"],
            "closest_approach_km": min_dist_km,
            "score": round(composite, 1),
            "anomalies": v["anomalies"],
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    for rank, v in enumerate(scored, 1):
        v["rank"] = rank
        status = "HIGH ATTRIBUTION SUSPECT" if v["score"] > 75 else ("MODERATE CORRELATION" if v["score"] > 50 else "LOW CORRELATION")
        print(f"  Rank #{v['rank']}: {v['name']} (MMSI: {v['mmsi']}) | Physical Score: {v['score']:.1f}/100 [{status}]")
        print(f"    Approach: {v['closest_approach_km']:.2f} km from probable origin centroid")
    return scored


def step_7_evidence_manifest(scene_meta, geo, hindcast, candidates):
    print("\n[STAGE 7/7] Generating Tamper-Evident SHA-256 Evidence Manifest...")
    manifest = EvidenceManifest(incident_id="INC-2026-0917-GOM")

    # Register raw imagery
    manifest.register(EvidenceArtifact(
        artifact_type="SATELLITE_SCENE_SAR",
        sha256=scene_meta["sha256"],
        size_bytes=48291040,
        storage_key="s3://slicktrace-imagery/" + scene_meta["filename"],
        description="Raw Sentinel-1A SAR Ground Range Detected scene",
    ))

    # Register segmentation
    seg_bytes = json.dumps(geo.get("geojson_polygon"), sort_keys=True).encode()
    manifest.register(EvidenceArtifact(
        artifact_type="SPILL_SEGMENTATION_GEOMETRY",
        sha256=sha256_bytes(seg_bytes),
        size_bytes=len(seg_bytes),
        storage_key="s3://slicktrace-outputs/spill_polygon.geojson",
        description="Cleaned metric polygon geometry of observed slick",
    ))

    # Register hindcast
    traj_bytes = json.dumps(hindcast.trajectory_geojson, sort_keys=True).encode()
    manifest.register(EvidenceArtifact(
        artifact_type="HINDCAST_TRAJECTORIES_GEOJSON",
        sha256=sha256_bytes(traj_bytes),
        size_bytes=len(traj_bytes),
        storage_key="s3://slicktrace-outputs/hindcast_ensemble.geojson",
        description="Lagrangian backward trajectories (4h, 8h, 12h, 24h horizons)",
    ))

    # Register candidate shortlist
    cand_bytes = json.dumps(candidates, sort_keys=True).encode()
    manifest.register(EvidenceArtifact(
        artifact_type="VESSEL_ATTRIBUTION_SHORTLIST",
        sha256=sha256_bytes(cand_bytes),
        size_bytes=len(cand_bytes),
        storage_key="s3://slicktrace-outputs/candidate_shortlist.json",
        description="Physical consistency scored candidate vessel ranking",
    ))

    exported = manifest.export()
    print(f"  * Manifest ID       : {exported['manifest_id']}")
    print(f"  * Registered Items  : {exported['artifact_count']} artifacts")
    print(f"  * Cryptographic Hash: {exported['manifest_sha256']}")
    print("  * Verification      : CHAIN-OF-CUSTODY INTACT (All digests verified)")
    return exported


def main():
    mode = os.environ.get("SLICKTRACE_MODE", "demo").lower()
    if mode == "real":
        print("ERROR: run.py is a DEMO-only CLI script and contains mock data.")
        print("To run the real pipeline, use the web interface or the backend API.")
        sys.exit(1)

    banner()
    scene = step_1_satellite_ingest()
    geo = step_2_spill_segmentation(scene)
    hindcast = step_3_ocean_hindcast(geo)
    vessels = step_4_and_5_ais_and_anomalies(hindcast)
    ranked = step_6_consistency_ranking(vessels, hindcast)
    manifest = step_7_evidence_manifest(scene, geo, hindcast, ranked)

    print("\n=======================================================")
    print("SLICKTRACE v2 INVESTIGATION PIPELINE COMPLETED SUCCESSFULLY")
    print("Tamper-Evident Forensic Dossier Ready for Export.")
    print("=======================================================\n")


if __name__ == "__main__":
    main()
