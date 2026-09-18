"""
SlickTrace v2 — Backend API Tests
"""
import pytest
from app.core.config import Settings, OperationMode


def test_settings_mode_defaults():
    settings = Settings(SLICKTRACE_MODE=OperationMode.REAL)
    assert settings.is_real_mode is True
    assert settings.is_demo_mode is False


def test_settings_demo_mode():
    settings = Settings(SLICKTRACE_MODE=OperationMode.DEMO)
    assert settings.is_demo_mode is True
    assert settings.is_real_mode is False


def test_unavailable_sources_reporting():
    settings = Settings(
        SLICKTRACE_MODE=OperationMode.REAL,
        CDSE_USERNAME=None,
        CMEMS_USERNAME=None,
        CDS_KEY=None,
    )
    unavailable = settings.get_unavailable_sources()
    assert "copernicus_dataspace" in unavailable
    assert "copernicus_marine" in unavailable
    assert "era5_cds" in unavailable


def test_evidence_manifest_hashing():
    from app.core.security import sha256_bytes, EvidenceManifest, EvidenceArtifact

    data = b"Sentinel-1 SAR Test Payload"
    h = sha256_bytes(data)
    assert len(h) == 64

    manifest = EvidenceManifest(incident_id="test-incident-uuid")
    art = EvidenceArtifact(
        artifact_type="satellite_imagery",
        sha256=h,
        size_bytes=len(data),
        storage_key="test/key.tif",
        description="Test SAR scene",
    )
    manifest.register(art)
    out = manifest.export()

    assert out["incident_id"] == "test-incident-uuid"
    assert out["artifact_count"] == 1
    assert "manifest_sha256" in out
    assert len(out["manifest_sha256"]) == 64


def test_evidence_registry_lifecycle_and_provenance():
    """Verify EvidenceRegistry calculates SHA-256 and tracks all 9 event types and fields."""
    from evidence.manifest.registry import EvidenceRegistry, EvidenceEventType

    reg = EvidenceRegistry(incident_id="incident-uuid-1234")

    # Record all 9 event types
    event_types = [
        EvidenceEventType.CREATED,
        EvidenceEventType.UPLOADED,
        EvidenceEventType.PROCESSED,
        EvidenceEventType.DETECTED,
        EvidenceEventType.DRIFT_ANALYZED,
        EvidenceEventType.AIS_QUERIED,
        EvidenceEventType.BEHAVIOR_ANALYZED,
        EvidenceEventType.VERIFIED,
        EvidenceEventType.EXPORTED,
    ]

    for et in event_types:
        evt = reg.record_event(
            event_type=et,
            source="test_pipeline_component",
            file_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            analysis_run_id="run-001",
            model_version="unetplusplus-v2",
            dataset_version="cdse-v1",
            software_version="2.0.0",
        )
        assert evt["event_type"] == et.value
        assert "event_hash" in evt
        assert len(evt["event_hash"]) == 64
        assert evt["file_hash"] == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    manifest = reg.build_manifest()
    assert manifest["package_type"] == "Tamper-evident evidence package"
    assert manifest["event_count"] == 9
    assert "manifest_sha256" in manifest
    assert len(manifest["manifest_sha256"]) == 64
    assert "admissibility" in manifest["disclaimer"].lower()

    # Verify manifest integrity
    assert EvidenceRegistry.verify_manifest(manifest) is True

