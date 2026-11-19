# GeoPulse — Functional Requirements

> **Document**: Functional Requirements Specification  
> **Project**: GeoPulse — Hyper-Local Retail Mobility Analytics  
> **Phase**: Phase 1 — Day 1  
> **Last Updated**: 2026-11-17  

---

## Module 1: Data Engineering & Spatial Processing

### FR-DE-001: Synthetic GPS Data Generation

| Field | Detail |
|-------|--------|
| **ID** | FR-DE-001 |
| **Title** | Synthetic GPS Mobility Data Generation |
| **Description** | Generate realistic anonymized GPS mobility data simulating user movement within a defined geographic study area |
| **Input** | Configuration parameters: user count, GPS points count, date range, bounding box, noise level |
| **Output** | `data/raw/gps_mobility.csv` with columns: user_id, timestamp, latitude, longitude, accuracy |
| **Acceptance Criteria** | Configurable volume; coordinates within study area; realistic timestamps; controlled noise/invalid records; generation summary report |

### FR-DE-002: Retail Store Data Generation

| Field | Detail |
|-------|--------|
| **ID** | FR-DE-002 |
| **Title** | Synthetic Retail Store Location Generation |
| **Description** | Generate synthetic retail store locations distributed across the study area with categories |
| **Input** | Configuration: store count, study area bounds, category distribution |
| **Output** | `data/reference/store_locations.csv` with columns: store_id, store_name, store_category, latitude, longitude, store_status |
| **Acceptance Criteria** | Unique store IDs (STR_ prefix); valid coordinates; multiple categories (grocery, fashion, electronics, pharmacy, convenience); realistic spatial distribution |

### FR-DE-003: Data Cleaning & Validation

| Field | Detail |
|-------|--------|
| **ID** | FR-DE-003 |
| **Title** | GPS and Store Data Cleaning Pipeline |
| **Description** | Validate, clean, and standardize raw datasets without modifying originals |
| **Input** | `data/raw/gps_mobility.csv`, `data/reference/store_locations.csv` |
| **Output** | `data/processed/cleaned_gps_mobility.csv`, `data/processed/cleaned_store_locations.csv`, `data/quality/data_quality_report.json`, `data/rejected/` |
| **Acceptance Criteria** | Validates lat [-90,90], lon [-180,180]; removes duplicates; handles missing values; generates quality report with counts; preserves rejected records |

### FR-DE-004: Haversine Distance Calculation

| Field | Detail |
|-------|--------|
| **ID** | FR-DE-004 |
| **Title** | Geographic Distance Calculation |
| **Description** | Calculate Haversine great-circle distance between GPS observations and store locations |
| **Input** | Cleaned GPS data, cleaned store locations |
| **Output** | Distance matrix or nearest-store assignments |
| **Acceptance Criteria** | Returns distance in kilometers; handles invalid inputs gracefully; vectorized for performance; tested against known coordinate pairs |

### FR-DE-005: Nearest Store Mapping

| Field | Detail |
|-------|--------|
| **ID** | FR-DE-005 |
| **Title** | GPS-to-Nearest-Store Assignment |
| **Description** | Map each GPS observation to its nearest retail store with distance and threshold flag |
| **Input** | Cleaned GPS data, store locations, configurable max distance threshold |
| **Output** | `data/processed/nearest_store_mapping.csv` with nearest_store_id, distance_km, within_distance_threshold |
| **Acceptance Criteria** | Every GPS point gets nearest store; configurable threshold (default 5 km); unmatched observations preserved; ties documented |

### FR-DE-006: Store Visit Detection

| Field | Detail |
|-------|--------|
| **ID** | FR-DE-006 |
| **Title** | Store Visit Detection from GPS Observations |
| **Description** | Detect store visits by analyzing consecutive GPS observations near a store exceeding minimum dwell time |
| **Input** | Nearest store mapping, configurable visit radius (50m), minimum dwell time (5 min) |
| **Output** | `data/processed/detected_store_visits.csv` with visit_id, user_id, store_id, arrival_time, departure_time, dwell_time_minutes |
| **Acceptance Criteria** | Proximity alone is not a visit; requires consecutive observations within radius; respects minimum dwell time; handles observation gaps; documents limitations |

### FR-DE-007: Apache Sedona Spatial Processing

| Field | Detail |
|-------|--------|
| **ID** | FR-DE-007 |
| **Title** | Geospatial Spatial Joins via Apache Sedona |
| **Description** | Perform spatial joins between GPS points and store/zone geometries using distributed processing |
| **Input** | Cleaned GPS data, store locations, zone boundaries |
| **Output** | `data/processed/sedona_spatial_results/` with enriched GPS data and spatial join results |
| **Acceptance Criteria** | Proper CRS handling (WGS 84); results consistent with Haversine within tolerance; environment validated before execution |

### FR-DE-008: Snowflake Data Integration

| Field | Detail |
|-------|--------|
| **ID** | FR-DE-008 |
| **Title** | Load Processed Data into Snowflake |
| **Description** | Load all processed datasets into Snowflake GEOPULSE_DB with proper schema structure |
| **Input** | All processed CSV files, Snowflake credentials (via .env) |
| **Output** | Populated RAW/STAGING/PROCESSED tables in Snowflake |
| **Acceptance Criteria** | Reusable connection logic; safe duplicate handling; record count validation; documented as BLOCKED if no credentials |

---

## Module 2: Analytics & Visualization

### FR-AV-001: Commercial Zoning Data Preparation

| Field | Detail |
|-------|--------|
| **ID** | FR-AV-001 |
| **Title** | Commercial Zone Data Preparation |
| **Description** | Prepare and enrich commercial zone boundary data for spatial analysis |
| **Input** | Zone definitions with geometry (WKT polygons) |
| **Output** | Processed zone data in `data/reference/` and Snowflake RAW |
| **Acceptance Criteria** | Valid polygon geometries; zone classification; area calculations |

### FR-AV-002: Store-Level Footfall Analytics

| Field | Detail |
|-------|--------|
| **ID** | FR-AV-002 |
| **Title** | Store-Level Footfall Aggregation |
| **Description** | Aggregate detected visits to produce per-store footfall metrics |
| **Input** | Detected store visits |
| **Output** | `mart_store_footfall_summary` with total visits, unique visitors, avg dwell time, peak hour |
| **Acceptance Criteria** | Accurate aggregation; handles stores with zero visits; daily and overall summaries |

### FR-AV-003: Hourly Footfall Analytics

| Field | Detail |
|-------|--------|
| **ID** | FR-AV-003 |
| **Title** | Hourly Traffic Pattern Analysis |
| **Description** | Analyze visit patterns by hour of day and day of week |
| **Input** | Detected store visits with timestamps |
| **Output** | `mart_hourly_traffic_patterns` with hour/day breakdown and percentage of daily traffic |
| **Acceptance Criteria** | 24-hour breakdown; day-of-week patterns; percentage calculations |

### FR-AV-004: dbt Transformation Models

| Field | Detail |
|-------|--------|
| **ID** | FR-AV-004 |
| **Title** | dbt SQL Transformation Pipeline |
| **Description** | Build dbt models: staging (clean/type), intermediate (aggregate), marts (business-ready) |
| **Input** | Snowflake RAW tables |
| **Output** | dbt models in `dbt_geopulse/models/` with staging/, intermediate/, marts/ |
| **Acceptance Criteria** | Follows dbt best practices; tested with dbt test; documented with YAML schema files |

### FR-AV-005: Store Catchment Analysis

| Field | Detail |
|-------|--------|
| **ID** | FR-AV-005 |
| **Title** | Store Catchment Area Mapping |
| **Description** | Define geographic catchment area for each store based on visitor origin locations |
| **Input** | Store visits with user GPS origins, configurable radius (5 km) |
| **Output** | `mart_store_catchment_areas` with catchment radius, user count, avg/max distance |
| **Acceptance Criteria** | Per-store catchment metrics; configurable radius; area calculation |

### FR-AV-006: Catchment Overlap Analysis

| Field | Detail |
|-------|--------|
| **ID** | FR-AV-006 |
| **Title** | Geographic Catchment Overlap Detection |
| **Description** | Identify store pairs with shared customers in overlapping catchment areas |
| **Input** | Store catchment data, store visits |
| **Output** | `mart_catchment_overlap` with store pairs, shared users, overlap percentage |
| **Acceptance Criteria** | Pairwise comparison; symmetric overlap percentages; distance between stores |

### FR-AV-007: Cannibalization Risk Assessment

| Field | Detail |
|-------|--------|
| **ID** | FR-AV-007 |
| **Title** | Retail Cannibalization Risk Scoring |
| **Description** | Score store pairs for cannibalization risk based on overlap, proximity, and category |
| **Input** | Catchment overlap, store metadata |
| **Output** | `mart_cannibalization_risk` with risk score, risk level (low/medium/high) |
| **Acceptance Criteria** | Multi-factor scoring; same-category amplification; threshold-based risk levels |

### FR-AV-008: Kepler.gl Interactive Dashboard

| Field | Detail |
|-------|--------|
| **ID** | FR-AV-008 |
| **Title** | Interactive Geospatial Dashboard |
| **Description** | Build Kepler.gl map visualizations with Plotly analytical charts |
| **Input** | All mart-level analytics data |
| **Output** | Interactive HTML dashboard in `dashboard/` |
| **Acceptance Criteria** | Store locations layer; heatmap layer; catchment area layer; interactive filtering |

### FR-AV-009: Business Insights & Recommendations

| Field | Detail |
|-------|--------|
| **ID** | FR-AV-009 |
| **Title** | Business Insights Report |
| **Description** | Generate data-driven business recommendations from analytics results |
| **Input** | All mart-level analytics |
| **Output** | Business insights report in `reports/` |
| **Acceptance Criteria** | Findings tied to data; recommendations are actionable; limitations stated |

---

## Module 3: Common Responsibilities

### FR-CM-001: Airflow DAG Creation

| Field | Detail |
|-------|--------|
| **ID** | FR-CM-001 |
| **Description** | Create Apache Airflow DAGs to orchestrate the full data pipeline |
| **Output** | DAG definitions in `airflow/dags/` |
| **Acceptance Criteria** | Task dependencies reflect data flow; error handling; idempotent tasks |

### FR-CM-002: Pipeline Integration

| Field | Detail |
|-------|--------|
| **ID** | FR-CM-002 |
| **Description** | Integrate Module 1 and Module 2 into a cohesive end-to-end pipeline |
| **Acceptance Criteria** | Data flows from generation through dashboard; contracts honored |

### FR-CM-003: End-to-End Testing

| Field | Detail |
|-------|--------|
| **ID** | FR-CM-003 |
| **Description** | Test the complete pipeline from data generation to dashboard output |
| **Acceptance Criteria** | All stages produce valid output; no data loss between stages |

### FR-CM-004: Documentation

| Field | Detail |
|-------|--------|
| **ID** | FR-CM-004 |
| **Description** | Maintain technical and user documentation throughout development |
| **Acceptance Criteria** | Architecture, data dictionary, setup instructions, API docs |

### FR-CM-005: Final Project Report

| Field | Detail |
|-------|--------|
| **ID** | FR-CM-005 |
| **Description** | Comprehensive project report covering methodology, findings, and recommendations |

### FR-CM-006: Final Presentation & Demo

| Field | Detail |
|-------|--------|
| **ID** | FR-CM-006 |
| **Description** | Live demonstration of the complete GeoPulse platform |
