import os
import logging
from typing import List
from datetime import datetime
import duckdb

logger = logging.getLogger(__name__)

class DuckDBAISAdapter:
    """
    Historical AIS subsystem using DuckDB Spatial.
    Normalizes MarineCadastre AccessAIS and bulk AIS datasets.
    """
    
    def __init__(self, db_path: str = "data/ais/slicktrace_ais.duckdb"):
        self.db_path = db_path
        self.conn = None
        
    def _get_connection(self):
        if self.conn is None:
            if not os.path.exists(self.db_path):
                logger.warning(f"AIS database {self.db_path} does not exist. Initializing empty.")
                os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self.conn = duckdb.connect(self.db_path, read_only=True)
            try:
                self.conn.execute("INSTALL spatial; LOAD spatial;")
            except Exception as e:
                logger.warning(f"Failed to load DuckDB spatial extension: {e}")
        return self.conn

    def query_vessels_in_origin_window(
        self,
        geometry_wkt: str,
        start_time: datetime,
        end_time: datetime,
        radius_km: float = 0.0
    ) -> List[dict]:
        """
        Query vessels matching spatial and temporal criteria.
        Returns ONLY vessels actually present in the dataset. Never invents vessels.
        """
        if not os.path.exists(self.db_path):
            logger.info("No historical AIS DuckDB database found.")
            return []
            
        conn = self._get_connection()
        
        # Verify table exists
        tables = conn.execute("SHOW TABLES").fetchall()
        if not any(t[0] == 'ais_positions' for t in tables):
            logger.info("Table 'ais_positions' does not exist in AIS database.")
            return []
            
        # Buffer the geometry if radius_km > 0
        # 1 degree lat is ~111km. For a rough bounding box filter, we use radius_km / 111.0.
        deg_buffer = radius_km / 111.0 if radius_km else 0.0
        
        # DuckDB Spatial querying against ais_positions
        query = """
        SELECT *
        FROM ais_positions
        WHERE timestamp_utc >= ? AND timestamp_utc <= ?
        AND ST_Intersects(
            ST_Point(longitude, latitude),
            ST_Buffer(ST_GeomFromText(?), ?)
        )
        """
        
        try:
            results = conn.execute(
                query, 
                [start_time, end_time, geometry_wkt, deg_buffer]
            ).fetchdf()
            
            if results.empty:
                return []
                
            # Convert NaN to None for dict representation
            results = results.replace({float('nan'): None})
            records = results.to_dict('records')
            
            # Format timestamp_utc as datetime
            for r in records:
                if r.get('timestamp_utc'):
                    r['timestamp_utc'] = r['timestamp_utc'].to_pydatetime()
                    
            return records
        except Exception as e:
            logger.error(f"Failed to query AIS data in DuckDB: {e}")
            return []
