"""
SlickTrace v2 — DuckDB Spatial AIS Query Engine

Performs spatiotemporal queries against the loaded AIS database to find
all vessels present within the hindcast origin window.

Uses DuckDB Spatial extension for efficient bounding box / radius filtering.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

import duckdb
from loguru import logger

from ais.ingest.marinecadastre import AIS_DB_PATH, get_duckdb_connection, init_ais_table


class AISQueryResult:
    def __init__(
        self,
        mmsi: str,
        vessel_name: Optional[str],
        vessel_type: Optional[str],
        imo: Optional[str],
        call_sign: Optional[str],
        length: Optional[float],
        beam: Optional[float],
        draft: Optional[float],
        positions: List[Dict[str, Any]],
        provider: str,
        dataset: str,
    ):
        self.mmsi = mmsi
        self.vessel_name = vessel_name
        self.vessel_type = vessel_type
        self.imo = imo
        self.call_sign = call_sign
        self.length = length
        self.beam = beam
        self.draft = draft
        self.positions = positions
        self.provider = provider
        self.dataset = dataset

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mmsi": self.mmsi,
            "vessel_name": self.vessel_name,
            "vessel_type": self.vessel_type,
            "imo": self.imo,
            "call_sign": self.call_sign,
            "length": self.length,
            "beam": self.beam,
            "draft": self.draft,
            "position_count": len(self.positions),
            "positions": self.positions,
            "provider": self.provider,
            "dataset": self.dataset,
        }


def query_vessels_in_origin_window(
    geometry: Any,
    time_start: datetime,
    time_end: datetime,
    radius_km: Optional[float] = None,
    db_path=None,
) -> tuple[List[AISQueryResult], str]:
    """
    Query AIS database for all vessels within the hindcast origin window.
    """
    db_path = db_path or AIS_DB_PATH

    if not db_path.exists():
        logger.warning("[AIS QUERY] No AIS database found. Upload AIS data first.")
        return [], "-- No AIS database available"

    conn = get_duckdb_connection(db_path)
    init_ais_table(conn)

    ts = time_start.strftime("%Y-%m-%d %H:%M:%S")
    te = time_end.strftime("%Y-%m-%d %H:%M:%S")

    geometry_wkt = geometry.wkt
    deg_buffer = (radius_km / 111.0) if radius_km else 0.0

    # Base query using Spatial extension
    sql = f"""
        SELECT
            mmsi,
            ANY_VALUE(vessel_name)  AS vessel_name,
            ANY_VALUE(vessel_type)  AS vessel_type,
            ANY_VALUE(imo)          AS imo,
            ANY_VALUE(call_sign)    AS call_sign,
            ANY_VALUE(length)       AS length,
            ANY_VALUE(beam)         AS beam,
            ANY_VALUE(draft)        AS draft,
            ANY_VALUE(provider)     AS provider,
            ANY_VALUE(dataset)      AS dataset,
            COUNT(*)                AS position_count,
            MIN(timestamp_utc)      AS first_seen,
            MAX(timestamp_utc)      AS last_seen,
            MIN(sog)                AS min_sog,
            MAX(sog)                AS max_sog,
            AVG(sog)                AS avg_sog
        FROM ais_positions
        WHERE timestamp_utc BETWEEN TIMESTAMP '{ts}' AND TIMESTAMP '{te}'
          AND mmsi IS NOT NULL
          AND ST_Intersects(
            ST_Point(longitude, latitude),
            ST_Buffer(ST_GeomFromText('{geometry_wkt}'), {deg_buffer})
          )
        GROUP BY mmsi ORDER BY position_count DESC
    """

    logger.info(f"[AIS QUERY] Executing spatial query: time={ts} to {te}")
    summary_df = conn.execute(sql).fetchdf()
    logger.info(f"[AIS QUERY] Found {len(summary_df)} unique vessels")

    results = []
    for _, row in summary_df.iterrows():
        mmsi = str(row["mmsi"])
        # Fetch individual positions for this vessel in the window
        pos_sql = f"""
            SELECT timestamp_utc, latitude, longitude, sog, cog, heading
            FROM ais_positions
            WHERE mmsi = '{mmsi}'
              AND timestamp_utc BETWEEN TIMESTAMP '{ts}' AND TIMESTAMP '{te}'
            ORDER BY timestamp_utc
        """
        pos_df = conn.execute(pos_sql).fetchdf()
        
        # Convert pandas NaN to None
        pos_df = pos_df.replace({float('nan'): None})
        positions = pos_df.to_dict(orient="records")
        
        # Convert timestamps to ISO strings for JSON serialization
        for p in positions:
            if hasattr(p.get("timestamp_utc"), "isoformat"):
                p["timestamp_utc"] = p["timestamp_utc"].isoformat()

        def _val(x):
            import math
            return x if x is not None and not (isinstance(x, float) and math.isnan(x)) else None

        results.append(AISQueryResult(
            mmsi=mmsi,
            vessel_name=_val(row.get("vessel_name")),
            vessel_type=_val(row.get("vessel_type")),
            imo=_val(row.get("imo")),
            call_sign=_val(row.get("call_sign")),
            length=_val(row.get("length")),
            beam=_val(row.get("beam")),
            draft=_val(row.get("draft")),
            positions=positions,
            provider=str(row.get("provider", "marinecadastre")),
            dataset=str(row.get("dataset", "bulk_ais")),
        ))

    conn.close()
    return results, sql
