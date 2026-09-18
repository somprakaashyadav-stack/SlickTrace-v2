"""
SlickTrace v2 — Security & Chain-of-Custody

Provides:
- SHA-256 file/bytes hashing
- Evidence artifact registration
- Tamper-evident manifest builder
- Chain-of-custody metadata recorder
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


def sha256_bytes(data: bytes) -> str:
    """Return hex SHA-256 digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    """Return hex SHA-256 digest of a file (streaming, memory-safe)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_stream(stream: BinaryIO) -> tuple[str, bytes]:
    """
    Read a stream, return (sha256_hex, raw_bytes).
    Stream is consumed fully.
    """
    h = hashlib.sha256()
    buf = bytearray()
    for chunk in iter(lambda: stream.read(65536), b""):
        h.update(chunk)
        buf.extend(chunk)
    return h.hexdigest(), bytes(buf)


class EvidenceArtifact:
    """Represents a single evidence artifact with cryptographic metadata."""

    def __init__(
        self,
        artifact_type: str,
        sha256: str,
        size_bytes: int,
        storage_key: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.artifact_id = str(uuid.uuid4())
        self.artifact_type = artifact_type
        self.sha256 = sha256
        self.size_bytes = size_bytes
        self.storage_key = storage_key
        self.description = description
        self.metadata = metadata or {}
        self.recorded_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "storage_key": self.storage_key,
            "description": self.description,
            "metadata": self.metadata,
            "recorded_at": self.recorded_at,
        }


class EvidenceManifest:
    """
    Tamper-evident evidence manifest for a single investigation incident.
    Each artifact is registered with its SHA-256 hash.
    The manifest itself is SHA-256 signed at export time.
    """

    def __init__(self, incident_id: str):
        self.manifest_id = str(uuid.uuid4())
        self.incident_id = incident_id
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.artifacts: List[EvidenceArtifact] = []

    def register(self, artifact: EvidenceArtifact) -> None:
        self.artifacts.append(artifact)
        logger.info(
            f"[MANIFEST] Registered {artifact.artifact_type} "
            f"sha256={artifact.sha256[:16]}... incident={self.incident_id}"
        )

    def export(self) -> Dict[str, Any]:
        """Export manifest as dict; computes manifest-level SHA-256."""
        body = {
            "manifest_id": self.manifest_id,
            "incident_id": self.incident_id,
            "created_at": self.created_at,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "artifact_count": len(self.artifacts),
            "artifacts": [a.to_dict() for a in self.artifacts],
        }
        body_bytes = json.dumps(body, sort_keys=True).encode()
        body["manifest_sha256"] = sha256_bytes(body_bytes)
        return body

    def export_json(self) -> str:
        return json.dumps(self.export(), indent=2)


class ChainOfCustody:
    """
    Records provenance of each pipeline step:
    who triggered it, what inputs, what outputs, timestamps.
    """

    def __init__(self, incident_id: str):
        self.incident_id = incident_id
        self.entries: List[Dict[str, Any]] = []

    def record(
        self,
        step: str,
        operator: str,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        notes: str = "",
    ) -> None:
        entry = {
            "entry_id": str(uuid.uuid4()),
            "step": step,
            "operator": operator,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "inputs": inputs,
            "outputs": outputs,
            "notes": notes,
        }
        self.entries.append(entry)
        logger.info(f"[CUSTODY] step={step} operator={operator}")

    def export(self) -> Dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "entry_count": len(self.entries),
            "entries": self.entries,
        }
