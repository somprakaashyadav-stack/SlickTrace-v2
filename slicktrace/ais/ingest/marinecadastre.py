"""
SlickTrace v2 — MarineCadastre Bulk AIS Downloader and DuckDB Loader

Downloads NOAA MarineCadastre bulk AIS data (CSV or Parquet format)
and loads it into DuckDB for spatial querying.

Data source: https://marinecadastre.gov/ais/
Format: Zone-based CSV files (UTM zones, daily/monthly)
No API key required — bulk download via HTTPS.
"""
from __future__ import annotations

import urllib.request
from pathlib import Path
from typing import Optional

import duckdb
from loguru import logger

# MarineCadastre AIS data base URL pattern
# Files are named: AIS_{YEAR}_{MONTH}_{ZONE}.zip
MARINECADASTRE_BASE_URL = "https://coast.noaa.gov/htdata/CMSP/AISDataHandler/{year}/AIS_{year}_{month:02d}_{zone}.zip"

AIS_DB_PATH = Path("data/ais/slicktrace_ais.duckdb")


class AISIngestError(Exception):
    pass


def get_duckdb_connection(db_path: Path = AIS_DB_PATH) -> duckdb.DuckDBPyConnection:
    """Return a DuckDB connection with spatial extension loaded."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(db_path))
    conn.execute("INSTALL spatial; LOAD spatial;")
    conn.execute("INSTALL httpfs; LOAD httpfs;")
    return conn


def init_ais_table(conn: duckdb.DuckDBPyConnection) -> None:
    """Create the AIS positions table if it does not exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ais_positions (
            mmsi VARCHAR NOT NULL,
            imo VARCHAR,
            vessel_name VARCHAR,
            call_sign VARCHAR,
            vessel_type VARCHAR,
            length DOUBLE,
            beam DOUBLE,
            draft DOUBLE,
            timestamp_utc TIMESTAMP NOT NULL,
            latitude DOUBLE NOT NULL,
            longitude DOUBLE NOT NULL,
            sog DOUBLE,
            cog DOUBLE,
            heading DOUBLE,
            provider VARCHAR DEFAULT 'marinecadastre',
            dataset VARCHAR DEFAULT 'bulk_ais'
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_ais_mmsi ON ais_positions (mmsi)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_ais_datetime ON ais_positions (timestamp_utc)
    """)
    logger.info("[AIS] ais_positions table initialised")


def load_csv_file(
    csv_path: Path,
    conn: duckdb.DuckDBPyConnection,
    source_label: str = "local_csv",
) -> int:
    """
    Load a CSV AIS file into the ais_positions DuckDB table.
    Expects standard MarineCadastre column names:
    MMSI, VesselName, VesselType, IMO, CallSign, BaseDateTime, LAT, LON, SOG, COG, Heading, Status

    Returns: number of rows inserted
    """
    if not csv_path.exists():
        raise AISIngestError(f"CSV file not found: {csv_path}")

    # Detect columns
    preview = conn.execute(f"SELECT * FROM read_csv_auto('{csv_path}') LIMIT 1").fetchdf()
    cols = [c.lower() for c in preview.columns]

    col_map = {
        "mmsi": next((c for c in cols if "mmsi" in c), None),
        "imo": next((c for c in cols if c == "imo"), None),
        "vessel_name": next((c for c in cols if "vesselname" in c or "vessel_name" in c), None),
        "call_sign": next((c for c in cols if "callsign" in c or "call_sign" in c), None),
        "vessel_type": next((c for c in cols if "vesseltype" in c or "vessel_type" in c), None),
        "length": next((c for c in cols if "length" in c), None),
        "beam": next((c for c in cols if "width" in c or "beam" in c), None),
        "draft": next((c for c in cols if "draft" in c), None),
        "timestamp_utc": next((c for c in cols if "datetime" in c or "timestamp" in c), None),
        "latitude": next((c for c in cols if c in ("lat", "latitude")), None),
        "longitude": next((c for c in cols if c in ("lon", "lng", "longitude")), None),
        "sog": next((c for c in cols if c == "sog"), None),
        "cog": next((c for c in cols if c == "cog"), None),
        "heading": next((c for c in cols if "heading" in c), None),
    }

    if not col_map["mmsi"] or not col_map["latitude"] or not col_map["longitude"] or not col_map["timestamp_utc"]:
        raise AISIngestError(
            f"CSV missing required columns. Found: {cols}. "
            "Expected at minimum: MMSI, LAT, LON, BaseDateTime"
        )

    def col(key: str) -> str:
        return f'"{col_map[key]}"' if col_map[key] else "NULL"

    sql = f"""
        INSERT INTO ais_positions
        SELECT
            CAST({col('mmsi')} AS VARCHAR),
            {col('imo')},
            {col('vessel_name')},
            {col('call_sign')},
            {col('vessel_type')},
            TRY_CAST({col('length')} AS DOUBLE),
            TRY_CAST({col('beam')} AS DOUBLE),
            TRY_CAST({col('draft')} AS DOUBLE),
            TRY_CAST({col('timestamp_utc')} AS TIMESTAMP),
            CAST({col('latitude')} AS DOUBLE),
            CAST({col('longitude')} AS DOUBLE),
            TRY_CAST({col('sog')} AS DOUBLE),
            TRY_CAST({col('cog')} AS DOUBLE),
            TRY_CAST({col('heading')} AS DOUBLE),
            'marinecadastre',
            '{source_label}'
        FROM read_csv_auto('{csv_path}')
        WHERE {col('latitude')} IS NOT NULL
          AND {col('longitude')} IS NOT NULL
          AND {col('mmsi')} IS NOT NULL
    """
    conn.execute(sql)
    count = conn.execute("SELECT changes()").fetchone()[0]
    logger.info(f"[AIS] Loaded {count} rows from {csv_path.name}")
    return count



def load_parquet_file(
    parquet_path: Path,
    conn: duckdb.DuckDBPyConnection,
    source_label: str = "local_parquet",
) -> int:
    """
    Load a Parquet AIS file into ais_positions.
    Same column mapping as CSV loader.
    """
    if not parquet_path.exists():
        raise AISIngestError(f"Parquet file not found: {parquet_path}")

    sql = f"""
        INSERT INTO ais_positions
        SELECT
            CAST(MMSI AS VARCHAR),
            IMO,
            VesselName,
            CallSign,
            VesselType,
            TRY_CAST(Length AS DOUBLE),
            TRY_CAST(Width AS DOUBLE),
            TRY_CAST(Draft AS DOUBLE),
            TRY_CAST(BaseDateTime AS TIMESTAMP),
            CAST(LAT AS DOUBLE),
            CAST(LON AS DOUBLE),
            TRY_CAST(SOG AS DOUBLE),
            TRY_CAST(COG AS DOUBLE),
            TRY_CAST(Heading AS DOUBLE),
            'marinecadastre',
            '{source_label}'
        FROM read_parquet('{parquet_path}')
        WHERE LAT IS NOT NULL AND LON IS NOT NULL AND MMSI IS NOT NULL
    """
    conn.execute(sql)
    count = conn.execute("SELECT changes()").fetchone()[0]
    logger.info(f"[AIS] Loaded {count} rows from {parquet_path.name}")
    return count



def download_marinecadastre_zone(
    year: int,
    month: int,
    zone: int,
    download_dir: Path,
) -> Optional[Path]:
    """
    Download a MarineCadastre AIS zip file for a given year/month/UTM zone.

    Returns path to downloaded zip, or None if download fails.
    Note: caller should extract and call load_csv_file() on the CSV inside.
    """
    url = MARINECADASTRE_BASE_URL.format(year=year, month=month, zone=zone)
    filename = f"AIS_{year}_{month:02d}_{zone}.zip"
    dest = download_dir / filename

    if dest.exists():
        logger.info(f"[AIS] Already downloaded: {dest}")
        return dest

    download_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"[AIS] Downloading from MarineCadastre: {url}")
    try:
        urllib.request.urlretrieve(url, str(dest))
        logger.info(f"[AIS] Download complete: {dest}")
        return dest
    except Exception as e:
        logger.error(f"[AIS] Download failed: {url} — {e}")
        return None
