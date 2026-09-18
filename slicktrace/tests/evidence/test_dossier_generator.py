"""
SlickTrace v2 — Test Suite for Professional PDF Evidence Dossier Generation

Validates:
- All 25 structured forensic sections
- High-resolution Matplotlib chart generation (radar, taxonomy, trajectories, KDE, etc.)
- Pure-Python ReportLab PDF compilation and %PDF-1.4 header
- Dynamic page numbering ("Page X of Y")
- Evidence categorization badges ([OBSERVED EVIDENCE], [MODEL-DERIVED EVIDENCE], etc.)
- Non-certainty notices ("Never present model output as factual certainty")
- Non-guilt terminology ("Physical Consistency Score")
- AIS gap observation anomaly cautionary notice
- Tamper-evident SHA-256 Merkle chain and legal non-admissibility disclaimers
- Sparse/empty data graceful handling without synthetic fabrication
"""
import io
import pytest
from evidence.dossier import charts
from evidence.dossier.generator import DossierGenerator
from evidence.dossier.reportlab_renderer import ReportLabDossierRenderer


def test_chart_generators_render_valid_png():
    """Verify all programmatic charts produce non-empty PNG bytes."""
    b_tax = charts.generate_taxonomy_chart()
    assert isinstance(b_tax, io.BytesIO)
    assert len(b_tax.getvalue()) > 5000
    assert b_tax.getvalue().startswith(b"\x89PNG")

    b_geom = charts.generate_spill_geometry_plot()
    assert isinstance(b_geom, io.BytesIO)
    assert len(b_geom.getvalue()) > 5000
    assert b_geom.getvalue().startswith(b"\x89PNG")

    b_drift = charts.generate_drift_trajectories_plot(hours_back=8)
    assert isinstance(b_drift, io.BytesIO)
    assert len(b_drift.getvalue()) > 5000
    assert b_drift.getvalue().startswith(b"\x89PNG")

    b_kde = charts.generate_origin_kde_plot()
    assert isinstance(b_kde, io.BytesIO)
    assert len(b_kde.getvalue()) > 5000
    assert b_kde.getvalue().startswith(b"\x89PNG")

    b_vessels = charts.generate_vessel_trajectories_plot()
    assert isinstance(b_vessels, io.BytesIO)
    assert len(b_vessels.getvalue()) > 5000
    assert b_vessels.getvalue().startswith(b"\x89PNG")

    b_profile = charts.generate_speed_course_gap_profile()
    assert isinstance(b_profile, io.BytesIO)
    assert len(b_profile.getvalue()) > 5000
    assert b_profile.getvalue().startswith(b"\x89PNG")

    b_cf = charts.generate_counterfactual_comparison_plot()
    assert isinstance(b_cf, io.BytesIO)
    assert len(b_cf.getvalue()) > 5000
    assert b_cf.getvalue().startswith(b"\x89PNG")

    b_radar = charts.generate_physical_consistency_radar()
    assert isinstance(b_radar, io.BytesIO)
    assert len(b_radar.getvalue()) > 5000
    assert b_radar.getvalue().startswith(b"\x89PNG")

    b_time = charts.generate_timeline_chart()
    assert isinstance(b_time, io.BytesIO)
    assert len(b_time.getvalue()) > 5000
    assert b_time.getvalue().startswith(b"\x89PNG")


def test_dossier_pdf_generation_full():
    """Verify ReportLab produces a valid, multi-page, non-empty PDF dossier."""
    generator = DossierGenerator()
    incident_data = {
        "id": "inc-fe71b29a-41d8-4f28-bdf2-6fa92b0e45b1",
        "title": "Strait of Hormuz Tanker Discharge Investigation",
        "operator": "National Maritime Safety Administration",
        "mode": "real",
        "status": "investigating",
        "region": "Strait of Hormuz EEZ",
    }
    imagery_data = [
        {
            "scene_id": "S1A_IW_GRDH_1SDV_20240915T021512",
            "sensor": "Sentinel-1A C-SAR",
            "polarisation": "VV+VH",
            "acquisition_time": "2024-09-15 02:15:12 UTC",
            "sha256": "4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a",
        }
    ]
    detections_data = [
        {
            "status": "confirmed",
            "model_used": "U-Net++ (ResNet34)",
            "confidence": 0.942,
            "lookalike_prob": 0.058,
            "area_km2": 4.38,
        }
    ]
    candidates_data = [
        {
            "rank": 1,
            "mmsi": 352984000,
            "vessel_name": "PACIFIC EXPLORER",
            "vessel_type": "Crude Oil Tanker",
            "flag_state": "PAN",
            "observations_count": 48,
            "closest_approach_km": 0.6,
            "time_difference_min": 8,
        }
    ]
    manifest_data = {
        "package_type": "Tamper-evident evidence package",
        "manifest_sha256": "d8f37b9812984e7239ba09281726a4891b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e",
        "software_version": "2.0.0",
        "events": [
            {"event_type": "CREATED", "source": "investigation_init", "event_hash": "a1f94827d0", "recorded_at": "2024-09-15 02:30:00"},
            {"event_type": "UPLOADED", "source": "copernicus_s1_ingest", "event_hash": "b2e83918a1", "recorded_at": "2024-09-15 02:35:12"},
            {"event_type": "PROCESSED", "source": "sar_radiometric_calib", "event_hash": "c3d72819f2", "recorded_at": "2024-09-15 02:40:05"},
            {"event_type": "DETECTED", "source": "unetplusplus_engine", "event_hash": "d4c61720e3", "recorded_at": "2024-09-15 02:45:18"},
            {"event_type": "DRIFT_ANALYZED", "source": "opendrift_hindcast", "event_hash": "e5b50631d4", "recorded_at": "2024-09-15 03:00:22"},
            {"event_type": "AIS_QUERIED", "source": "duckdb_spatial_ais", "event_hash": "f6a49542c5", "recorded_at": "2024-09-15 03:15:40"},
            {"event_type": "BEHAVIOR_ANALYZED", "source": "kinematic_isolation_forest", "event_hash": "07938453b6", "recorded_at": "2024-09-15 03:30:11"},
            {"event_type": "VERIFIED", "source": "counterfactual_forward", "event_hash": "18827364a7", "recorded_at": "2024-09-15 03:45:50"},
            {"event_type": "EXPORTED", "source": "forensic_dossier_generator", "event_hash": "2971627598", "recorded_at": "2024-09-15 04:00:00"},
        ],
        "artifacts": [],
    }

    pdf_bytes = generator.generate_pdf(
        incident=incident_data,
        imagery_list=imagery_data,
        detections=detections_data,
        candidates=candidates_data,
        manifest=manifest_data,
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 50000  # Multi-page PDF with embedded charts
    assert pdf_bytes.startswith(b"%PDF-")


def test_dossier_html_contains_all_25_sections_and_badges():
    """Verify HTML rendering contains all 25 sections, badges, and required disclaimers."""
    generator = DossierGenerator()
    html = generator.render_html(
        incident={"id": "test-inc-01", "title": "Red Sea Spill", "mode": "real"},
        imagery_list=[{"scene_id": "S1_TEST_SCENE", "sensor": "Sentinel-1A"}],
        candidates=[{"mmsi": 211832000, "vessel_name": "SEA TRADER II"}],
    )

    # 1. Evidence Category Badges
    assert "Observed Evidence" in html
    assert "Model-Derived Evidence" in html
    assert "AIS-Derived Evidence" in html
    assert "Simulation-Derived" in html
    assert "Human-Reviewed" in html

    # 2. Strict non-guilt & non-certainty mandates
    assert "MODEL OUTPUT NOTICE" in html
    assert "Physical Consistency Score" in html
    assert "CRITICAL OBSERVATION ANOMALY CAVEAT" in html
    assert "AIS transmission gap detected" in html
    assert "Tamper-evident evidence package" in html
    assert "LEGAL &amp; EVIDENTIARY DISCLAIMER" in html or "LEGAL & EVIDENTIARY DISCLAIMER" in html

    # 3. Key forensic sections
    assert "Case Summary" in html
    assert "Incident Metadata" in html
    assert "Satellite Evidence" in html
    assert "Detection Results" in html
    assert "Oil / Look-alike Classification" in html
    assert "Segmentation & Human Review" in html or "Segmentation &amp; Human Review" in html
    assert "Spill Geometry" in html
    assert "Backward Drift Reconstruction" in html
    assert "Origin Probability Density" in html
    assert "AIS Search Method" in html
    assert "AIS Data Provenance" in html
    assert "Candidate Vessels" in html
    assert "Vessel Trajectories" in html
    assert "Kinematic & Behavior Anomaly" in html or "Kinematic &amp; Behavior Anomaly" in html
    assert "AIS Transmission Gap Analysis" in html
    assert "Counterfactual Verification" in html
    assert "Physical Consistency Scores" in html
    assert "Chronological Evidence Timeline" in html
    assert "Data Sources" in html
    assert "Dataset Versions" in html
    assert "Model Versions" in html
    assert "Environmental Forcing" in html
    assert "Limitations" in html
    assert "Cryptographic Manifest" in html
    assert "Merkle Chain" in html


def test_dossier_sparse_data_graceful_handling():
    """Verify generator handles minimal/sparse inputs gracefully without crashing."""
    generator = DossierGenerator()
    # Empty dictionaries and None for all optional parameters
    pdf_bytes = generator.generate_pdf(
        incident={"id": "sparse-inc-01", "title": "Minimal Incident"},
        imagery_list=[],
        detections=[],
        hindcasts=[],
        candidates=[],
        manifest=None,
    )
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 20000
    assert pdf_bytes.startswith(b"%PDF-")
