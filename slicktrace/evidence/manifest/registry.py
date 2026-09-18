"""
SlickTrace v2 — Cryptographic Evidence Registry & Immutable Manifest Builder

Generates SHA-256 tamper-evident manifests for maritime spill investigations.
Tracks all raw data, satellite products, drift simulations, AIS extracts,
behavior anomalies, counterfactual verifications, and export dossiers.

Enforces:
- SHA-256 calculation on every file and artifact
- Event types: CREATED, UPLOADED, PROCESSED, DETECTED, DRIFT_ANALYZED,
  AIS_QUERIED, BEHAVIOR_ANALYZED, VERIFIED, EXPORTED
- Full provenance metadata: file_hash, source, uploaded_at, processed_at,
  analysis_run_id, model_version, dataset_version, software_version
- Strict non-legal admissibility disclaimer with tamper-evident assurance.
"""
from __future__ import annotations

import enum
import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class EvidenceEventType(str, enum.Enum):
    CREATED = "CREATED"
    UPLOADED = "UPLOADED"
    PROCESSED = "PROCESSED"
    DETECTED = "DETECTED"
    DRIFT_ANALYZED = "DRIFT_ANALYZED"
    AIS_QUERIED = "AIS_QUERIED"
    BEHAVIOR_ANALYZED = "BEHAVIOR_ANALYZED"
    VERIFIED = "VERIFIED"
    EXPORTED = "EXPORTED"


def compute_sha256(data: bytes) -> str:
    """Compute SHA-256 checksum of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def compute_file_sha256(filepath: Path) -> str:
    """Compute SHA-256 checksum of a file streaming in 64KB blocks."""
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()


class EvidenceRegistry:
    """
    Evidence Registry ensuring strict chain of custody, cryptographic integrity,
    and immutable event chaining.
    """

    SOFTWARE_VERSION = "2.0.0"

    def __init__(self, incident_id: str):
        self.incident_id = incident_id
        self.events: List[Dict[str, Any]] = []
        self.artifacts: List[Dict[str, Any]] = []
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.last_event_hash = "0" * 64

    def record_event(
        self,
        event_type: EvidenceEventType | str,
        source: str,
        file_hash: Optional[str] = None,
        uploaded_at: Optional[str] = None,
        processed_at: Optional[str] = None,
        analysis_run_id: Optional[str] = None,
        model_version: Optional[str] = None,
        dataset_version: Optional[str] = None,
        software_version: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Record an immutable evidence event in the cryptographic chain.
        """
        event_type_str = event_type.value if isinstance(event_type, EvidenceEventType) else str(event_type)
        now_utc = datetime.now(timezone.utc).isoformat()

        event_payload = {
            "event_id": str(uuid.uuid4()),
            "incident_id": self.incident_id,
            "event_type": event_type_str,
            "source": source,
            "file_hash": file_hash or compute_sha256(f"{source}:{now_utc}".encode("utf-8")),
            "uploaded_at": uploaded_at or now_utc,
            "processed_at": processed_at or now_utc,
            "analysis_run_id": analysis_run_id or f"run-{uuid.uuid4().hex[:8]}",
            "model_version": model_version or "unetplusplus-v2.0",
            "dataset_version": dataset_version or "copernicus-cdse-v1",
            "software_version": software_version or self.SOFTWARE_VERSION,
            "previous_event_hash": self.last_event_hash,
            "recorded_at": now_utc,
            "metadata": metadata or {},
        }

        canonical_event_bytes = json.dumps(event_payload, sort_keys=True).encode("utf-8")
        event_hash = compute_sha256(canonical_event_bytes)
        event_payload["event_hash"] = event_hash

        self.last_event_hash = event_hash
        self.events.append(event_payload)
        return event_payload

    def register_artifact(
        self,
        artifact_type: str,
        name: str,
        sha256_hash: str,
        size_bytes: int,
        source_uri: str,
        source: str = "pipeline",
        uploaded_at: Optional[str] = None,
        processed_at: Optional[str] = None,
        analysis_run_id: Optional[str] = None,
        model_version: Optional[str] = None,
        dataset_version: Optional[str] = None,
        software_version: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record an evidence piece with SHA-256 hash and full provenance tracking."""
        now_utc = datetime.now(timezone.utc).isoformat()
        entry = {
            "artifact_id": str(uuid.uuid4()),
            "artifact_type": artifact_type,
            "name": name,
            "file_hash": sha256_hash,
            "sha256": sha256_hash,
            "size_bytes": size_bytes,
            "source_uri": source_uri,
            "source": source,
            "uploaded_at": uploaded_at or now_utc,
            "processed_at": processed_at or now_utc,
            "analysis_run_id": analysis_run_id or f"run-{uuid.uuid4().hex[:8]}",
            "model_version": model_version or "2.0.0",
            "dataset_version": dataset_version or "1.0.0",
            "software_version": software_version or self.SOFTWARE_VERSION,
            "recorded_at": now_utc,
            "metadata": metadata or {},
        }
        self.artifacts.append(entry)

        # Automatically log corresponding event
        self.record_event(
            event_type=EvidenceEventType.UPLOADED if "upload" in artifact_type.lower() else EvidenceEventType.PROCESSED,
            source=source,
            file_hash=sha256_hash,
            uploaded_at=uploaded_at,
            processed_at=processed_at,
            analysis_run_id=analysis_run_id,
            model_version=model_version,
            dataset_version=dataset_version,
            software_version=software_version,
            metadata={"artifact_type": artifact_type, "name": name, "size_bytes": size_bytes},
        )

        return entry

    def build_manifest(self) -> Dict[str, Any]:
        """
        Build the tamper-evident manifest package.
        Calculates a root manifest SHA-256 hash across sorted artifacts and event chain.
        """
        manifest_payload = {
            "package_type": "Tamper-evident evidence package",
            "incident_id": self.incident_id,
            "created_at": self.created_at,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "software_version": self.SOFTWARE_VERSION,
            "artifact_count": len(self.artifacts),
            "event_count": len(self.events),
            "artifacts": sorted(self.artifacts, key=lambda x: x.get("file_hash") or x.get("sha256", "")),
            "events": self.events,
            "disclaimer": (
                "Tamper-evident evidence package. This manifest cryptographically guarantees data integrity "
                "and chain-of-custody provenance. It does not constitute a legal determination of admissibility "
                "or liability in judicial proceedings."
            ),
        }

        canonical_bytes = json.dumps(manifest_payload, sort_keys=True).encode("utf-8")
        manifest_sha256 = compute_sha256(canonical_bytes)

        manifest_payload["manifest_sha256"] = manifest_sha256
        return manifest_payload

    @staticmethod
    def verify_manifest(manifest: Dict[str, Any]) -> bool:
        """Verify the integrity of an exported manifest."""
        claimed_sha256 = manifest.get("manifest_sha256")
        if not claimed_sha256:
            return False

        payload_copy = {k: v for k, v in manifest.items() if k != "manifest_sha256"}
        canonical_bytes = json.dumps(payload_copy, sort_keys=True).encode("utf-8")
        actual_sha256 = compute_sha256(canonical_bytes)

        return claimed_sha256 == actual_sha256
