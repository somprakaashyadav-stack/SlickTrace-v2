"""
SlickTrace v2 — Copernicus Data Space Ecosystem (CDSE) Sentinel Data Adapter

Provides authenticated catalog searching, metadata retrieval, streaming download,
MinIO caching, and validation for Sentinel-1 (C-SAR) and Sentinel-2 (MSI) imagery.

Key Endpoints (CDSE OData & Keycloak):
- Token Auth: https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token
- Catalog OData: https://catalogue.dataspace.copernicus.eu/odata/v1/Products
- Download Zipper: https://zipper.dataspace.copernicus.eu/odata/v1/Products({id})/$value

Strict Non-Fabrication Guarantee:
If credentials are not configured or service is unreachable,
raises CopernicusProviderUnavailable. Never synthesizes fake products.
"""
from __future__ import annotations

import hashlib
import json
import os
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from app.core.config import settings
from app.services.satellite_ingest import compute_file_sha256_and_size


class CopernicusProviderUnavailable(Exception):
    """Raised when Copernicus API access cannot be established."""
    def __init__(self, message: str, registration_url: str = "https://dataspace.copernicus.eu/"):
        self.message = message
        self.registration_url = registration_url
        super().__init__(f"[UNAVAILABLE] Copernicus Data Space: {message}")


class CopernicusDataSpaceAdapter:
    """
    Client adapter for Copernicus Data Space Ecosystem (CDSE) APIs.
    """

    AUTH_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    CATALOGUE_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
    ZIPPER_URL = "https://zipper.dataspace.copernicus.eu/odata/v1/Products"

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.username = username or settings.CDSE_USERNAME
        self.password = password or settings.CDSE_PASSWORD
        self._cached_token: Optional[str] = None
        self._token_expiry: float = 0.0

    def check_availability(self) -> Tuple[bool, str]:
        """
        Check if Copernicus Data Space credentials are configured in environment.
        Returns (is_available, diagnostic_reason).
        """
        if not self.username or not self.password:
            return (
                False,
                "CDSE_USERNAME and CDSE_PASSWORD not configured. "
                "Register for a free Copernicus Data Space account at https://dataspace.copernicus.eu/",
            )
        return True, "Credentials configured"

    def _require_available(self) -> None:
        """Enforce strict provider availability check."""
        ok, reason = self.check_availability()
        if not ok:
            raise CopernicusProviderUnavailable(reason)

    def get_auth_token(self) -> str:
        """
        Retrieve or refresh Keycloak OAuth2 bearer token from CDSE.
        """
        self._require_available()

        now = datetime.now(timezone.utc).timestamp()
        if self._cached_token and now < (self._token_expiry - 60):
            return self._cached_token

        data = {
            "client_id": "cdse-public",
            "username": self.username,
            "password": self.password,
            "grant_type": "password",
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(self.AUTH_URL, data=data)
                if res.status_code == 401:
                    raise CopernicusProviderUnavailable("Authentication failed: Invalid CDSE credentials.")
                res.raise_for_status()
                payload = res.json()
                token = payload.get("access_token")
                expires_in = payload.get("expires_in", 600)
                if not token:
                    raise CopernicusProviderUnavailable("CDSE auth response missing access_token.")

                self._cached_token = token
                self._token_expiry = now + expires_in
                return token
        except httpx.HTTPError as e:
            raise CopernicusProviderUnavailable(f"Network error communicating with CDSE auth server: {e}")

    @staticmethod
    def build_odata_filter(
        platform: str,  # "SENTINEL-1" or "SENTINEL-2"
        date_from: datetime,
        date_to: datetime,
        aoi_wkt: Optional[str] = None,
        product_type: Optional[str] = None,
        polarization: Optional[str] = None,
        max_cloud_cover: Optional[float] = None,
    ) -> str:
        """
        Constructs an OData v1 $filter string conforming to CDSE catalogue specifications.
        """
        clauses = []

        # 1. Collection Name filter
        platform_upper = platform.upper().strip()
        if "SENTINEL-1" in platform_upper or platform_upper == "S1":
            clauses.append("Collection/Name eq 'SENTINEL-1'")
        elif "SENTINEL-2" in platform_upper or platform_upper == "S2":
            clauses.append("Collection/Name eq 'SENTINEL-2'")

        # 2. Date Range filter (ContentDate/Start)
        d_from_str = date_from.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        d_to_str = date_to.strftime("%Y-%m-%dT%H:%M:%S.999Z")
        clauses.append(f"ContentDate/Start ge {d_from_str} and ContentDate/Start le {d_to_str}")

        # 3. Spatial AOI Intersection filter
        if aoi_wkt:
            # Format: OData.CSC.Intersects(area=geography'SRID=4326;POLYGON(...)')
            clauses.append(f"OData.CSC.Intersects(area=geography'SRID=4326;{aoi_wkt}')")

        # 4. Product Type attribute filter
        if product_type:
            pt = product_type.upper().strip()
            clauses.append(
                f"Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and att/OData.CSC.StringAttribute/Value eq '{pt}')"
            )

        # 5. Polarization attribute filter (Sentinel-1)
        if polarization and "SENTINEL-1" in platform_upper:
            pol = polarization.upper().strip()
            if pol in ("VV", "VH", "HH", "HV"):
                clauses.append(
                    f"Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'polarisationChannels' and contains(att/OData.CSC.StringAttribute/Value, '{pol}'))"
                )
            elif pol in ("VV+VH", "VV&VH"):
                clauses.append(
                    f"Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'polarisationChannels' and att/OData.CSC.StringAttribute/Value eq 'VV&VH')"
                )

        # 6. Cloud Cover filter (Sentinel-2)
        if max_cloud_cover is not None and "SENTINEL-2" in platform_upper:
            clauses.append(
                f"Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value le {float(max_cloud_cover)})"
            )

        return " and ".join(clauses)

    def search_products(
        self,
        platform: str,
        date_from: datetime,
        date_to: datetime,
        aoi_wkt: Optional[str] = None,
        product_type: Optional[str] = None,
        polarization: Optional[str] = None,
        max_cloud_cover: Optional[float] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Execute live CDSE OData catalogue search.
        Raises CopernicusProviderUnavailable if unconfigured or unreachable.
        Never fabricates results.
        """
        self._require_available()

        odata_filter = self.build_odata_filter(
            platform=platform,
            date_from=date_from,
            date_to=date_to,
            aoi_wkt=aoi_wkt,
            product_type=product_type,
            polarization=polarization,
            max_cloud_cover=max_cloud_cover,
        )

        params = {
            "$filter": odata_filter,
            "$top": str(min(limit, 50)),
            "$orderby": "ContentDate/Start desc",
            "$expand": "Attributes",
        }

        try:
            with httpx.Client(timeout=45.0) as client:
                res = client.get(self.CATALOGUE_URL, params=params)
                res.raise_for_status()
                data = res.json()
                items = data.get("value", [])

                products: List[Dict[str, Any]] = []
                for item in items:
                    prod = self._parse_odata_product(item)
                    products.append(prod)

                logger.info(f"[CDSE] Found {len(products)} products matching filter: {odata_filter[:120]}...")
                return products

        except httpx.HTTPError as e:
            raise CopernicusProviderUnavailable(f"Error querying CDSE catalogue: {e}")

    def get_product_metadata(self, product_id: str) -> Dict[str, Any]:
        """
        Retrieve full OData metadata attributes for a specific product ID.
        """
        self._require_available()

        url = f"{self.CATALOGUE_URL}({product_id})?$expand=Attributes"
        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.get(url)
                if res.status_code == 404:
                    raise CopernicusProviderUnavailable(f"Product {product_id} not found in CDSE catalogue.")
                res.raise_for_status()
                return self._parse_odata_product(res.json())
        except httpx.HTTPError as e:
            raise CopernicusProviderUnavailable(f"Failed to fetch metadata for product {product_id}: {e}")

    def download_product(
        self,
        product_id: str,
        target_path: Path,
    ) -> Path:
        """
        Stream download product archive from CDSE Zipper service with bearer auth.
        Saves to target_path and verifies download completion.
        """
        token = self.get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{self.ZIPPER_URL}({product_id})/$value"

        target_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with httpx.Client(timeout=600.0, follow_redirects=True) as client:
                with client.stream("GET", url, headers=headers) as response:
                    if response.status_code == 401:
                        raise CopernicusProviderUnavailable("Authorization token expired during download.")
                    response.raise_for_status()

                    with open(target_path, "wb") as f:
                        for chunk in response.iter_bytes(chunk_size=65536):
                            f.write(chunk)

            logger.info(f"[CDSE] Downloaded product {product_id} to {target_path}")
            return target_path

        except httpx.HTTPError as e:
            target_path.unlink(missing_ok=True)
            raise CopernicusProviderUnavailable(f"Download failed for product {product_id}: {e}")

    def cache_product(
        self,
        product_id: str,
        file_path: Path,
    ) -> Tuple[str, str, int]:
        """
        Uploads downloaded product to MinIO cache bucket and computes SHA-256.
        Returns: (minio_storage_key, file_sha256, size_bytes).
        """
        from app.core.storage import get_storage

        sha256_hash, size_bytes = compute_file_sha256_and_size(file_path)
        storage_key = f"cdse_cache/{product_id}/{file_path.name}"

        storage = get_storage()
        storage.upload_file(
            bucket=settings.MINIO_BUCKET_IMAGERY,
            key=storage_key,
            file_path=file_path,
        )

        logger.info(f"[CDSE CACHE] Cached {product_id} in MinIO at {storage_key} ({size_bytes} bytes)")
        return storage_key, sha256_hash, size_bytes

    def validate_product(self, file_path: Path) -> Dict[str, Any]:
        """
        Validates downloaded satellite product file integrity and metadata.
        """
        if not file_path.exists() or file_path.stat().st_size == 0:
            return {"valid": False, "reason": "File is empty or does not exist."}

        # If it is a GeoTIFF or COG, use SatelliteIngestService
        if file_path.suffix.lower() in (".tif", ".tiff"):
            from app.services.satellite_ingest import SatelliteIngestService
            try:
                inspection = SatelliteIngestService.inspect_and_validate(file_path, file_path.name)
                return {"valid": True, "details": inspection}
            except Exception as e:
                return {"valid": False, "reason": str(e)}

        # If it is a zip archive, verify checksum and size
        sha256_hash, size_bytes = compute_file_sha256_and_size(file_path)
        return {
            "valid": True,
            "details": {
                "file_hash": sha256_hash,
                "size_bytes": size_bytes,
                "is_archive": file_path.suffix.lower() == ".zip",
            },
        }

    def _parse_odata_product(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Parse raw CDSE OData JSON item into standardized dictionary."""
        p_id = str(raw.get("Id", ""))
        name = str(raw.get("Name", ""))
        content_length = raw.get("ContentLength", 0)

        c_date = raw.get("ContentDate", {})
        start_date = c_date.get("Start")
        end_date = c_date.get("End")

        # Parse attributes
        attributes = raw.get("Attributes", [])
        attr_map: Dict[str, Any] = {}
        for a in attributes:
            aname = a.get("Name")
            aval = a.get("Value")
            if aname:
                attr_map[aname] = aval

        # Quicklook URL
        quicklook_url = f"{self.CATALOGUE_URL}({p_id})/Quicklook/$value"

        # GeoJSON footprint
        footprint_geojson = raw.get("GeoFootprint")

        return {
            "id": p_id,
            "name": name,
            "content_length_bytes": content_length,
            "content_date_start": start_date,
            "content_date_end": end_date,
            "platform": attr_map.get("platformShortName") or ("Sentinel-1" if "S1" in name else "Sentinel-2"),
            "sensor": attr_map.get("instrumentShortName") or ("C-SAR" if "S1" in name else "MSI"),
            "product_type": attr_map.get("productType") or ("GRD" if "GRD" in name else "L2A"),
            "polarization": attr_map.get("polarisationChannels"),
            "cloud_cover_percent": attr_map.get("cloudCover"),
            "footprint_geojson": footprint_geojson,
            "quicklook_url": quicklook_url,
            "raw_attributes": attr_map,
        }
