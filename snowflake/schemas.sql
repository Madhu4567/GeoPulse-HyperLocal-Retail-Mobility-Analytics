-- =============================================================================
-- GeoPulse Snowflake Database Schema DDL
-- Database: GEOPULSE_DB
-- Phase 2: Data Engineering & Spatial Processing Tables
-- =============================================================================

-- 1. Database & Warehouse Setup
CREATE DATABASE IF NOT EXISTS GEOPULSE_DB;
CREATE WAREHOUSE IF NOT EXISTS GEOPULSE_WH
    WITH WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND = 300
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'GeoPulse analytics compute warehouse';

USE DATABASE GEOPULSE_DB;

-- 2. Schemas
CREATE SCHEMA IF NOT EXISTS RAW COMMENT = 'Raw landing zone for unprocessed CSV mobility data';
CREATE SCHEMA IF NOT EXISTS STAGING COMMENT = 'Cleaned, typed, deduplicated staging views and tables';
CREATE SCHEMA IF NOT EXISTS PROCESSED COMMENT = 'Spatial join associations, nearest store mappings, and visit events';
CREATE SCHEMA IF NOT EXISTS ANALYTICS COMMENT = 'Final analytical marts for Kepler.gl dashboards and business reports';

-- 3. File Formats & Stages
CREATE OR REPLACE FILE FORMAT RAW.CSV_FORMAT
    TYPE = 'CSV'
    FIELD_DELIMITER = ','
    RECORD_DELIMITER = '\n'
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    TRIM_SPACE = TRUE
    NULL_IF = ('', 'NULL', 'null', 'NaN', 'None')
    DATE_FORMAT = 'YYYY-MM-DD'
    TIMESTAMP_FORMAT = 'YYYY-MM-DD"T"HH24:MI:SS"Z"';

CREATE OR REPLACE STAGE RAW.DATA_STAGE
    FILE_FORMAT = RAW.CSV_FORMAT
    COMMENT = 'Internal stage for CSV data uploads';

-- =============================================================================
-- RAW SCHEMA TABLES
-- =============================================================================

-- RAW.GPS_MOBILITY: Raw GPS sensor observations
CREATE TABLE IF NOT EXISTS RAW.GPS_MOBILITY (
    user_id             VARCHAR(50),
    timestamp           VARCHAR(50),
    latitude            VARCHAR(50),
    longitude           VARCHAR(50),
    accuracy            VARCHAR(50),
    location_id         VARCHAR(50),
    _ingested_at        TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
) COMMENT = 'Raw mobility pings ingested directly from edge sensors or mobile log exports';

-- RAW.STORE_LOCATIONS: Raw store catalog
CREATE TABLE IF NOT EXISTS RAW.STORE_LOCATIONS (
    store_id            VARCHAR(50),
    store_name          VARCHAR(150),
    store_category      VARCHAR(100),
    latitude            VARCHAR(50),
    longitude           VARCHAR(50),
    store_status        VARCHAR(50),
    _ingested_at        TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
) COMMENT = 'Raw retail store locations and operational metadata';

-- =============================================================================
-- STAGING SCHEMA TABLES
-- =============================================================================

-- STAGING.CLEANED_GPS_MOBILITY: Sanitized, typed, deduplicated GPS pings
CREATE TABLE IF NOT EXISTS STAGING.CLEANED_GPS_MOBILITY (
    user_id             VARCHAR(50) NOT NULL,
    timestamp           TIMESTAMP_NTZ NOT NULL,
    latitude            FLOAT NOT NULL,
    longitude           FLOAT NOT NULL,
    accuracy            FLOAT,
    location_id         VARCHAR(50),
    _loaded_at          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT pk_stg_gps PRIMARY KEY (user_id, timestamp)
)
CLUSTER BY (DATE_TRUNC('DAY', timestamp), user_id)
COMMENT = 'Cleaned and validated GPS observations conforming to WGS84 coordinates';

-- STAGING.CLEANED_STORE_LOCATIONS: Validated retail store master
CREATE TABLE IF NOT EXISTS STAGING.CLEANED_STORE_LOCATIONS (
    store_id            VARCHAR(50) NOT NULL,
    store_name          VARCHAR(150) NOT NULL,
    store_category      VARCHAR(100) NOT NULL,
    latitude            FLOAT NOT NULL,
    longitude           FLOAT NOT NULL,
    store_status        VARCHAR(50) NOT NULL,
    _loaded_at          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT pk_stg_stores PRIMARY KEY (store_id)
) COMMENT = 'Validated retail store master records with verified WGS84 coordinates';

-- =============================================================================
-- PROCESSED SCHEMA TABLES
-- =============================================================================

-- PROCESSED.NEAREST_STORE_MAPPING: Vectorized proximity associations
CREATE TABLE IF NOT EXISTS PROCESSED.NEAREST_STORE_MAPPING (
    user_id                     VARCHAR(50) NOT NULL,
    timestamp                   TIMESTAMP_NTZ NOT NULL,
    latitude                    FLOAT NOT NULL,
    longitude                   FLOAT NOT NULL,
    accuracy                    FLOAT,
    nearest_store_id            VARCHAR(50) NOT NULL,
    distance_km                 FLOAT NOT NULL,
    within_distance_threshold   BOOLEAN NOT NULL,
    store_name                  VARCHAR(150),
    store_category              VARCHAR(100),
    _processed_at               TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY (DATE_TRUNC('DAY', timestamp), nearest_store_id)
COMMENT = 'GPS observations mapped to geographically nearest retail store with Haversine distance';

-- PROCESSED.DETECTED_STORE_VISITS: Confirmed dwell visits
CREATE TABLE IF NOT EXISTS PROCESSED.DETECTED_STORE_VISITS (
    visit_id            VARCHAR(50) NOT NULL,
    user_id             VARCHAR(50) NOT NULL,
    store_id            VARCHAR(50) NOT NULL,
    arrival_time        TIMESTAMP_NTZ NOT NULL,
    departure_time      TIMESTAMP_NTZ NOT NULL,
    dwell_time_minutes  FLOAT NOT NULL,
    observation_count   INTEGER NOT NULL,
    min_distance_km     FLOAT NOT NULL,
    visit_date          DATE NOT NULL,
    _processed_at       TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT pk_visits PRIMARY KEY (visit_id)
)
CLUSTER BY (visit_date, store_id)
COMMENT = 'Verified store visits confirmed via spatial radius (50m) and dwell duration (>= 5 min)';

-- PROCESSED.SPATIAL_RESULTS: Apache Sedona spatial join matches
CREATE TABLE IF NOT EXISTS PROCESSED.SPATIAL_RESULTS (
    user_id             VARCHAR(50) NOT NULL,
    timestamp           TIMESTAMP_NTZ NOT NULL,
    gps_latitude        FLOAT NOT NULL,
    gps_longitude       FLOAT NOT NULL,
    store_id            VARCHAR(50) NOT NULL,
    store_name          VARCHAR(150),
    store_category      VARCHAR(100),
    store_latitude      FLOAT NOT NULL,
    store_longitude     FLOAT NOT NULL,
    distance_meters     FLOAT NOT NULL,
    distance_km         FLOAT NOT NULL,
    spatial_match       BOOLEAN NOT NULL,
    _processed_at       TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY (DATE_TRUNC('DAY', timestamp), store_id)
COMMENT = 'Sedona point-in-radius spatial join results between GPS pings and store footprints';
