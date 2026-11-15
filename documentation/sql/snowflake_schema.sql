-- ============================================================
-- GeoPulse — Snowflake Schema DDL
-- ============================================================
-- Project:  GeoPulse — Hyper-Local Retail Mobility Analytics
-- Phase:    Day 3 — Database & Schema Design
-- Status:   DRAFT — Do NOT execute against a live Snowflake instance
-- Date:     2026-11-15
-- ============================================================

-- ============================================================
-- 1. DATABASE
-- ============================================================

CREATE DATABASE IF NOT EXISTS GEOPULSE_DB
    COMMENT = 'GeoPulse — Hyper-Local Retail Mobility Analytics database';

USE DATABASE GEOPULSE_DB;

-- ============================================================
-- 2. WAREHOUSE
-- ============================================================

CREATE WAREHOUSE IF NOT EXISTS GEOPULSE_WH
    WITH
        WAREHOUSE_SIZE      = 'X-SMALL'
        AUTO_SUSPEND        = 300          -- seconds (5 minutes)
        AUTO_RESUME         = TRUE
        INITIALLY_SUSPENDED = TRUE
        COMMENT             = 'Compute warehouse for GeoPulse analytics workloads';

-- ============================================================
-- 3. SCHEMAS
-- ============================================================

CREATE SCHEMA IF NOT EXISTS GEOPULSE_DB.RAW
    COMMENT = 'Raw ingested data — unmodified source files loaded via COPY INTO';

CREATE SCHEMA IF NOT EXISTS GEOPULSE_DB.STAGING
    COMMENT = 'Cleaned, typed, and validated data — managed by dbt staging models';

CREATE SCHEMA IF NOT EXISTS GEOPULSE_DB.INTERMEDIATE
    COMMENT = 'Business-logic aggregations and spatial joins — managed by dbt';

CREATE SCHEMA IF NOT EXISTS GEOPULSE_DB.MARTS
    COMMENT = 'Analytics-ready tables consumed by dashboards and reports — managed by dbt';

-- ============================================================
-- 4. FILE FORMATS
-- ============================================================

USE SCHEMA GEOPULSE_DB.RAW;

CREATE FILE FORMAT IF NOT EXISTS csv_format
    TYPE                    = 'CSV'
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    SKIP_HEADER             = 1
    NULL_IF                 = ('', 'NULL', 'null', 'None')
    TRIM_SPACE              = TRUE
    ERROR_ON_COLUMN_COUNT_MISMATCH = TRUE
    DATE_FORMAT             = 'YYYY-MM-DD'
    TIMESTAMP_FORMAT        = 'YYYY-MM-DDTHH24:MI:SS.FF3'
    COMMENT                 = 'Standard CSV format for GeoPulse data ingestion';

-- ============================================================
-- 5. INTERNAL STAGES
-- ============================================================

CREATE STAGE IF NOT EXISTS GEOPULSE_DB.RAW.gps_stage
    FILE_FORMAT = csv_format
    COMMENT     = 'Stage for GPS mobility CSV files';

CREATE STAGE IF NOT EXISTS GEOPULSE_DB.RAW.store_stage
    FILE_FORMAT = csv_format
    COMMENT     = 'Stage for retail store CSV files';

CREATE STAGE IF NOT EXISTS GEOPULSE_DB.RAW.zone_stage
    FILE_FORMAT = csv_format
    COMMENT     = 'Stage for commercial zone CSV files';

CREATE STAGE IF NOT EXISTS GEOPULSE_DB.RAW.visits_stage
    FILE_FORMAT = csv_format
    COMMENT     = 'Stage for processed store visit CSV files';

-- ============================================================
-- 6. RAW TABLES
-- ============================================================

-- ------------------------------------------------------------
-- 6.1  raw_gps_mobility
-- ------------------------------------------------------------
-- Synthetic GPS pings representing user mobility events.
-- Source: Module 1 — Synthetic GPS Data Generation
-- Contract: DC-001
-- Expected volume: ~250,000 rows
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS GEOPULSE_DB.RAW.raw_gps_mobility (
    user_id     VARCHAR(50)     NOT NULL
        COMMENT 'Unique user identifier (USR_ prefix)',

    timestamp   TIMESTAMP_NTZ   NOT NULL
        COMMENT 'UTC timestamp of the GPS ping',

    latitude    FLOAT           NOT NULL
        COMMENT 'WGS 84 latitude in decimal degrees (-90 to 90)',

    longitude   FLOAT           NOT NULL
        COMMENT 'WGS 84 longitude in decimal degrees (-180 to 180)',

    accuracy    FLOAT
        COMMENT 'GPS accuracy radius in meters (nullable)',

    _loaded_at  TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP()
        COMMENT 'Metadata: timestamp when the row was loaded into Snowflake',

    -- Constraints
    CONSTRAINT pk_raw_gps_mobility PRIMARY KEY (user_id, timestamp)
)
COMMENT = 'Raw GPS mobility pings — unmodified source data from synthetic generation'
;

-- ------------------------------------------------------------
-- 6.2  raw_retail_stores
-- ------------------------------------------------------------
-- Retail store master data with geographic coordinates.
-- Source: Module 1 — Retail Store Data Generation
-- Contract: DC-002
-- Expected volume: 50–200 rows
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS GEOPULSE_DB.RAW.raw_retail_stores (
    store_id        VARCHAR(50)     NOT NULL
        COMMENT 'Unique store identifier (STR_ prefix)',

    store_name      VARCHAR(255)    NOT NULL
        COMMENT 'Human-readable store name',

    latitude        FLOAT           NOT NULL
        COMMENT 'Store location latitude — WGS 84 decimal degrees',

    longitude       FLOAT           NOT NULL
        COMMENT 'Store location longitude — WGS 84 decimal degrees',

    store_category  VARCHAR(50)     NOT NULL
        COMMENT 'Business category: grocery, fashion, electronics, restaurant, pharmacy, convenience, department_store',

    opening_date    DATE
        COMMENT 'Date the store opened (nullable)',

    store_status    VARCHAR(20)     NOT NULL    DEFAULT 'active'
        COMMENT 'Operational status: active, inactive, closed',

    _loaded_at      TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP()
        COMMENT 'Metadata: timestamp when the row was loaded into Snowflake',

    -- Constraints
    CONSTRAINT pk_raw_retail_stores PRIMARY KEY (store_id)
)
COMMENT = 'Raw retail store master data — unmodified source from synthetic generation'
;

-- ------------------------------------------------------------
-- 6.3  raw_commercial_zones
-- ------------------------------------------------------------
-- Commercial zone boundary definitions with WKT geometry.
-- Source: Module 2 — Commercial Zoning Data Prep
-- Contract: DC-003
-- Expected volume: 10–50 rows
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS GEOPULSE_DB.RAW.raw_commercial_zones (
    zone_id     VARCHAR(50)         NOT NULL
        COMMENT 'Unique zone identifier (ZN_ prefix)',

    zone_name   VARCHAR(255)        NOT NULL
        COMMENT 'Human-readable zone name',

    zone_type   VARCHAR(50)         NOT NULL
        COMMENT 'Zone classification: mall, high_street, retail_park, market, commercial_district',

    geometry    VARCHAR(16777216)    NOT NULL
        COMMENT 'Zone boundary as WKT POLYGON or MULTIPOLYGON (WGS 84)',

    area_sq_km  FLOAT               NOT NULL
        COMMENT 'Zone area in square kilometers',

    _loaded_at  TIMESTAMP_NTZ       DEFAULT CURRENT_TIMESTAMP()
        COMMENT 'Metadata: timestamp when the row was loaded into Snowflake',

    -- Constraints
    CONSTRAINT pk_raw_commercial_zones PRIMARY KEY (zone_id)
)
COMMENT = 'Raw commercial zone boundaries — WKT geometry with zone metadata'
;

-- ============================================================
-- 7. RAW HANDOFF TABLE (Store Visits)
-- ============================================================
-- Processed store visit events — the key handoff from Module 1
-- to Module 2. Loaded from CSV produced by nearest-store
-- mapping and visit detection logic.
-- Contract: DC-004
-- Expected volume: ~20,000–100,000 rows
-- ============================================================

CREATE TABLE IF NOT EXISTS GEOPULSE_DB.RAW.raw_store_visits (
    visit_id            VARCHAR(100)    NOT NULL
        COMMENT 'Unique visit identifier (VST_ prefix)',

    user_id             VARCHAR(50)     NOT NULL
        COMMENT 'User who made the visit (FK to raw_gps_mobility)',

    store_id            VARCHAR(50)     NOT NULL
        COMMENT 'Store visited (FK to raw_retail_stores)',

    arrival_time        TIMESTAMP_NTZ   NOT NULL
        COMMENT 'Visit start time in UTC',

    departure_time      TIMESTAMP_NTZ   NOT NULL
        COMMENT 'Visit end time in UTC',

    dwell_time_minutes  FLOAT           NOT NULL
        COMMENT 'Visit duration in minutes',

    distance_km         FLOAT           NOT NULL
        COMMENT 'Haversine distance from user to store in kilometers',

    visit_date          DATE            NOT NULL
        COMMENT 'Date of the visit (derived from arrival_time)',

    _loaded_at          TIMESTAMP_NTZ   DEFAULT CURRENT_TIMESTAMP()
        COMMENT 'Metadata: timestamp when the row was loaded into Snowflake',

    -- Constraints
    CONSTRAINT pk_raw_store_visits PRIMARY KEY (visit_id)
)
COMMENT = 'Raw store visit events — Module 1 to Module 2 handoff data (Contract DC-004)'
;

-- ============================================================
-- 8. CLUSTERING KEYS (optional at current scale)
-- ============================================================
-- At ~250K rows, clustering is not strictly necessary.
-- These statements are included for documentation and can be
-- enabled when data volume grows.
-- ============================================================

-- ALTER TABLE GEOPULSE_DB.RAW.raw_gps_mobility
--     CLUSTER BY (timestamp, user_id);

-- ALTER TABLE GEOPULSE_DB.RAW.raw_store_visits
--     CLUSTER BY (visit_date, store_id);

-- ============================================================
-- 9. SAMPLE COPY INTO STATEMENTS
-- ============================================================
-- These are template commands for loading data from stages.
-- Adjust file paths as needed when actual files are staged.
-- ============================================================

/*
-- Load GPS mobility data
COPY INTO GEOPULSE_DB.RAW.raw_gps_mobility (user_id, timestamp, latitude, longitude, accuracy)
    FROM @GEOPULSE_DB.RAW.gps_stage
    FILE_FORMAT = (FORMAT_NAME = 'csv_format')
    ON_ERROR = 'SKIP_FILE';

-- Load retail store data
COPY INTO GEOPULSE_DB.RAW.raw_retail_stores (store_id, store_name, latitude, longitude, store_category, opening_date, store_status)
    FROM @GEOPULSE_DB.RAW.store_stage
    FILE_FORMAT = (FORMAT_NAME = 'csv_format')
    ON_ERROR = 'SKIP_FILE';

-- Load commercial zone data
COPY INTO GEOPULSE_DB.RAW.raw_commercial_zones (zone_id, zone_name, zone_type, geometry, area_sq_km)
    FROM @GEOPULSE_DB.RAW.zone_stage
    FILE_FORMAT = (FORMAT_NAME = 'csv_format')
    ON_ERROR = 'SKIP_FILE';

-- Load processed store visits (Module 1 → Module 2 handoff)
COPY INTO GEOPULSE_DB.RAW.raw_store_visits (visit_id, user_id, store_id, arrival_time, departure_time, dwell_time_minutes, distance_km, visit_date)
    FROM @GEOPULSE_DB.RAW.visits_stage
    FILE_FORMAT = (FORMAT_NAME = 'csv_format')
    ON_ERROR = 'SKIP_FILE';
*/

-- ============================================================
-- END OF DDL
-- ============================================================
