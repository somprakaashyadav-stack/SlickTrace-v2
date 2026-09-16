import json
from pathlib import Path
from typing import Dict, Any, List, Optional

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "data" / "sample"

class DemoService:
    def __init__(self, sample_dir: Path = SAMPLE_DIR):
        self.sample_dir = sample_dir

    def _load_json(self, filename: str) -> Any:
        filepath = self.sample_dir / filename
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def get_demo_spill(self) -> Dict[str, Any]:
        """Returns synthetic oil spill observation data."""
        return self._load_json("spill.json")

    def get_demo_vessels(self) -> List[Dict[str, Any]]:
        """Returns metadata for 8+ vessels."""
        return self._load_json("vessels.json")

    def get_demo_ais_tracks(self) -> List[Dict[str, Any]]:
        """Returns detailed AIS trajectories for all vessels."""
        return self._load_json("ais_tracks.json")

    def get_demo_metocean(self) -> Dict[str, Any]:
        """Returns wind and ocean current vectors."""
        return self._load_json("metocean.json")

    # --- PLATFORM SUMMARY HELPERS ---

    def get_spill_summary(self) -> Dict[str, Any]:
        spill = self.get_demo_spill()
        return {
          "slick_id": spill.get("spill_id", "SLICK-IN-2026-009"),
          "scene_id": "S1B_IW_GRDH_1SDV_20260912T143000_MUMBAI",
          "satellite": "Sentinel-1B",
          "detection_time": spill.get("timestamp", "2026-09-12T14:30:00Z"),
          "center_lat": spill.get("latitude", 18.9100),
          "center_lon": spill.get("longitude", 72.3500),
          "area_sq_km": spill.get("area_km2", 14.85),
          "estimated_volume_m3": 450.0,
          "confidence_score": spill.get("confidence", 0.94),
          "thick_spot_ratio": 0.28,
          "polygon": spill.get("polygon", [])
        }

    def get_drift_simulation(self) -> Dict[str, Any]:
        met = self.get_demo_metocean()
        spill = self.get_demo_spill()
        return {
            "slick_id": spill.get("spill_id", "SLICK-IN-2026-009"),
            "direction": "backward",
            "hours_modeled": 12,
            "particle_count": 150,
            "wind_speed_knots": met.get("wind", {}).get("speed_knots", 14.2),
            "wind_direction_deg": met.get("wind", {}).get("direction_deg", 210.0),
            "current_speed_knots": met.get("current", {}).get("speed_knots", 1.4),
            "current_direction_deg": met.get("current", {}).get("direction_deg", 245.0),
            "origin_ellipse": {
              "center_lat": 18.8450,
              "center_lon": 72.2480,
              "major_axis_km": 4.8,
              "minor_axis_km": 2.2,
              "orientation_deg": 235.0,
              "estimated_release_time": "2026-09-12T02:30:00Z"
            },
            "trajectories": [
              [
                {"step": 0, "time": "2026-09-12T14:30:00Z", "lat": 18.9100, "lon": 72.3500},
                {"step": 1, "time": "2026-09-12T11:30:00Z", "lat": 18.8920, "lon": 72.3240},
                {"step": 2, "time": "2026-09-12T08:30:00Z", "lat": 18.8750, "lon": 72.2980},
                {"step": 3, "time": "2026-09-12T05:30:00Z", "lat": 18.8580, "lon": 72.2700},
                {"step": 4, "time": "2026-09-12T02:30:00Z", "lat": 18.8450, "lon": 72.2480}
              ]
            ]
        }

    def get_ais_vessels(self) -> list:
        tracks = self.get_demo_ais_tracks()
        vessels_meta = {v["mmsi"]: v for v in self.get_demo_vessels()}
        result = []
        for t in tracks:
            mmsi = t["mmsi"]
            meta = vessels_meta.get(mmsi, {})
            # Adapt path to legacy schema lat/lon
            legacy_path = []
            for pt in t["path"]:
                legacy_path.append({
                    "timestamp": pt["timestamp"],
                    "lat": pt["latitude"],
                    "lon": pt["longitude"],
                    "speed_knots": pt["speed_knots"],
                    "heading_deg": pt["heading_deg"],
                    "course_deg": pt["course_deg"]
                })
            
            result.append({
                "mmsi": mmsi,
                "vessel_name": t["vessel_name"],
                "vessel_type": t["vessel_type"],
                "flag": meta.get("flag", "Unknown"),
                "imo": 9000000 + mmsi % 10000,
                "closest_distance_km": round(float(0.45 if mmsi == 419001234 else (2.1 if mmsi == 419003333 else (3.1 if mmsi == 419005678 else 10.5))), 2),
                "time_of_closest_approach": "2026-09-12T02:35:00Z",
                "path": legacy_path
            })
        return result

    def get_suspect_rankings(self) -> list:
        vessels = self.get_demo_vessels()
        tracks = {t["mmsi"]: t for t in self.get_demo_ais_tracks()}
        
        rankings = []
        # Score calculation for each vessel based on properties
        for idx, v in enumerate(vessels):
            mmsi = v["mmsi"]
            track = tracks.get(mmsi, {})
            has_gap = track.get("has_ais_gap", False)
            has_dev = track.get("has_course_deviation", False)
            phys_inconsistent = track.get("physical_inconsistency", False)
            
            if mmsi == 419001234: # MV Ocean Titan
                composite = 94.8
                risk = "CRITICAL"
                anomaly_desc = f"AIS Transponder turned OFF for {track.get('gap_duration_mins', 45)} mins during discharge window; Speed drop to 1.8 kn"
                rank = 1
            elif mmsi == 419005678: # MT Pearl Trader
                composite = 68.4
                risk = "MODERATE"
                anomaly_desc = "Significant course alteration (35 deg deviation) near origin zone"
                rank = 2
            elif mmsi == 419003333: # MV Arabian Wave
                composite = 52.0
                risk = "MODERATE"
                anomaly_desc = "Physically inconsistent trajectory (transiting 16.5 kn SW directly against current/wind drift axis)"
                rank = 3
            elif mmsi == 419008888: # SS Sagar Ratna
                composite = 45.2
                risk = "LOW"
                anomaly_desc = "Offshore rig supply maneuver in spatial vicinity"
                rank = 4
            elif mmsi == 419007777: # Matsya Kanya 04
                composite = 28.5
                risk = "LOW"
                anomaly_desc = "Erratic low-speed fishing trawling"
                rank = 5
            elif mmsi == 419009876: # CSCL Star Voyager
                composite = 22.0
                risk = "LOW"
                anomaly_desc = "Steady transit in commercial shipping corridor 8 km away"
                rank = 6
            elif mmsi == 419004444: # MV Sea Pioneer
                composite = 18.0
                risk = "NEGLIGIBLE"
                anomaly_desc = "Bulk carrier commercial transit"
                rank = 7
            else: # INS Taragiri
                composite = 12.0
                risk = "NEGLIGIBLE"
                anomaly_desc = "Routine naval coastal patrol"
                rank = 8

            rankings.append({
                "rank": rank,
                "mmsi": mmsi,
                "vessel_name": v["vessel_name"],
                "vessel_type": v["vessel_type"],
                "flag": v["flag"],
                "composite_score": composite,
                "spatial_score": round(max(10.0, composite * 1.05), 1),
                "temporal_score": round(max(10.0, composite * 0.95), 1),
                "anomaly_score": 92.0 if has_gap else (65.0 if has_dev else (40.0 if phys_inconsistent else 15.0)),
                "discharge_risk_score": 90.0 if "Tanker" in v["vessel_type"] else 20.0,
                "risk_level": risk,
                "ais_gap_detected": has_gap,
                "ais_gap_duration_mins": track.get("gap_duration_mins", 0),
                "speed_anomaly": anomaly_desc
            })

        rankings.sort(key=lambda x: x["rank"])
        return rankings

    def get_physics_verification(self) -> Dict[str, Any]:
        return {
            "vessel_mmsi": 419001234,
            "vessel_name": "MV Ocean Titan",
            "forward_simulation_match_index": 0.942,
            "mean_spatial_error_km": 0.38,
            "hydrodynamic_confidence": 95.6,
            "verification_status": "HIGHLY_VERIFIED_ORIGIN_MATCH",
            "comparison_particles": [
              {"time": "2026-09-12T02:35:00Z", "sim_lat": 18.8450, "sim_lon": 72.2480, "obs_lat": 18.8450, "obs_lon": 72.2480},
              {"time": "2026-09-12T05:30:00Z", "sim_lat": 18.8590, "sim_lon": 72.2710, "obs_lat": 18.8580, "obs_lon": 72.2700},
              {"time": "2026-09-12T08:30:00Z", "sim_lat": 18.8760, "sim_lon": 72.2990, "obs_lat": 18.8750, "obs_lon": 72.2980},
              {"time": "2026-09-12T11:30:00Z", "sim_lat": 18.8930, "sim_lon": 72.3250, "obs_lat": 18.8920, "obs_lon": 72.3240},
              {"time": "2026-09-12T14:30:00Z", "sim_lat": 18.9110, "sim_lon": 72.3510, "obs_lat": 18.9100, "obs_lon": 72.3500}
            ]
        }

    def get_evidence_report(self) -> Dict[str, Any]:
        spill = self.get_demo_spill()
        rankings = self.get_suspect_rankings()
        prime = rankings[0] if rankings else {}
        return {
            "incident_id": spill.get("spill_id", "SLICK-IN-2026-009"),
            "dossier_reference": f"SLICKTRACE-DOSSIER-{spill.get('spill_id', 'SLICK-009')}-2026",
            "generated_at": "2026-09-14T00:00:00Z",
            "spill_summary": self.get_spill_summary(),
            "prime_suspect": prime,
            "drift_physics_summary": self.get_drift_simulation().get("origin_ellipse", {}),
            "verification_status": self.get_physics_verification().get("verification_status", "VERIFIED"),
            "download_urls": {
                "json": f"/api/reports/{spill.get('spill_id', 'SLICK-009')}/export?format=json",
                "pdf": f"/api/reports/{spill.get('spill_id', 'SLICK-009')}/export?format=pdf"
            }
        }

demo_service = DemoService()
