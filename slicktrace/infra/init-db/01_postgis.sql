-- SlickTrace v2 — PostgreSQL/PostGIS initialization
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Confirm
SELECT PostGIS_version();
