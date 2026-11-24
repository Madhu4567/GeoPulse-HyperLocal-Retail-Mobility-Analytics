# GeoPulse AI Project Memory

> **Notice:** This file serves as the permanent external memory, development context, and state tracker for AI agents collaborating on the **GeoPulse – Hyper-Local Retail Mobility Analytics** platform. Every AI session MUST read this file before beginning work and update it before completing a session.

---

## 1. Project Overview
- **Project Name:** GeoPulse – Hyper-Local Retail Mobility Analytics
- **Project Objective:** Convert anonymized synthetic GPS mobility streams, retail store locations, and commercial zoning geometries into actionable business insights regarding footfall, catchment basins, territory overlap, and cannibalization.
- **Business Problem:** Retailers lack transparent, hyper-local intelligence to measure true store catchment boundaries, understand visitor dwell behavior, prevent self-cannibalization between nearby franchise stores, and identify high-potential expansion zones.
- **Target Users:** Retail portfolio strategists, franchise planners, commercial real estate developers, and marketing analysts.
- **Expected Outcomes:** Cleaned mobility datasets, Haversine nearest-store proximity mapping, visit candidate dwell detection, Apache Sedona spatial joins, Snowflake DW integration, dbt analytical marts, and interactive Kepler.gl dashboards.

---

## 2. Technology Stack

| Technology | Purpose | Module | Version / Target |
|---|---|---|---|
| **Python** | Primary development language & pipeline logic | Cross-Module | 3.12 (via codex runtime) |
| **Pandas** | Tabular cleaning, manipulation, and transformations | Module 1 & 2 | 3.0.1 |
| **NumPy** | Vectorized mathematical operations & Haversine | Module 1 | 2.3.5 |
| **Haversine** | Great-circle geographic distance calculations | Module 1 | Custom vectorized engine |
| **Apache Sedona / Spatial Engine** | Spatial joins, point geometry & radius joins | Module 1 | Sedona ready + Local Spatial Fallback |
| **Snowflake** | Cloud Data Warehouse (RAW, STAGING, PROCESSED, ANALYTICS) | Module 1 & 2 | DDL schemas & loaders ready |
| **dbt (dbt-snowflake)** | In-warehouse SQL transformations (Staging, Int, Marts) | Module 2 | Ready for Phase 3 |
| **Kepler.gl** | WebGL geospatial map rendering | Module 2 | Ready for Phase 4 |
| **Plotly** | Time-series, hourly distribution & footfall metrics | Module 2 | Ready for Phase 4 |
| **unittest / pytest** | Automated test suite | Module 3 | 13/13 passing tests |

---

## 3. Project Architecture
The platform operates on an **8-Layer Architecture**:
1. **Data Source Layer:** Synthetic GPS mobility (`data/raw/gps_mobility.csv`), retail store locations (`data/reference/store_locations.csv`).
2. **Data Engineering Layer:** `data_engineering/cleaning/gps_cleaner.py` and `store_cleaner.py` routing invalid rows to `data/rejected/`.
3. **Spatial Processing Layer:** Vectorized Haversine distance (`data_engineering/spatial/haversine.py`), nearest-store mapping (`nearest_store.py`), visit dwell time detection (`visit_detection.py`), Apache Sedona / spatial join engine (`sedona_processor.py`).
4. **Data Warehouse Layer:** Snowflake (`GEOPULSE_DB`) schemas: `RAW`, `STAGING`, `PROCESSED`, and `ANALYTICS`. Connection and loaders in `snowflake/`.
5. **dbt Transformation Layer:** SQL models converting processed visits into staging, intermediate aggregations, and dimensional marts (Phase 3).
6. **Analytics Layer:** Footfall statistics, hourly distributions, 5km catchment radius delineation, and cannibalization scoring (Phase 3).
7. **Dashboard Layer:** Kepler.gl interactive map views + Plotly analytical charts (Phase 4).
8. **Orchestration Layer:** Apache Airflow DAGs triggering generation, cleaning, loading, and dbt runs (Phase 4).

---

## 4. Repository Structure

```text
c:\Users\yash\geoplus\
├── data/
│   ├── raw/                  # gps_mobility.csv (25,152 rows), gps_generation_summary.json
│   ├── processed/            # cleaned_gps_mobility.csv (22,991 rows), cleaned_store_locations.csv (30 rows),
│   │                         # nearest_store_mapping.csv (22,991 rows), detected_store_visits.csv (3,487 rows),
│   │                         # sedona_spatial_results/ (spatially_enriched_gps.csv, store_proximity_spatial_join.csv)
│   ├── reference/            # store_locations.csv (30 stores)
│   ├── rejected/             # rejected_gps_records.csv (2,161 rows), rejected_store_records.csv (0 rows)
│   └── quality/              # data_quality_report.json
├── data_engineering/
│   ├── generation/           # gps_generator.py, store_generator.py
│   ├── cleaning/             # gps_cleaner.py, store_cleaner.py
│   ├── spatial/              # haversine.py, nearest_store.py, visit_detection.py, sedona_processor.py
│   └── validation/           # data_quality.py
├── src/                      # Scaffold package bridges
│   ├── data_generation/
│   ├── data_quality/
│   ├── spatial_processing/
│   └── analytics/
├── snowflake/                # connection.py, load_data.py, schemas.sql
├── dbt_geopulse/             # dbt models (staging, intermediate, marts), tests, macros
├── airflow/
│   └── dags/                 # pipeline orchestration DAGs
├── dashboard/                # Kepler.gl and Plotly visual interfaces
├── documentation/            # Complete Phase 1 & 2 architecture & contract docs
├── config/                   # settings.py, __init__.py
├── tests/                    # test_generation.py, test_cleaning.py, test_haversine.py,
│                             # test_nearest_store.py, test_visit_detection.py, test_sedona.py, test_project_scaffold.py
├── .env.example              # environment configuration template
├── .gitignore                # git exclusion rules
├── requirements.txt          # Python dependencies
├── README.md                 # Developer & user documentation
└── AI_README.md              # AI Project Memory
```

---

## 5. Team Responsibilities
- **Module 1 (Other Team Member):** Data Engineering & Spatial Processing (GPS data generation, store data generation, data cleaning, Haversine calculation, nearest-store mapping, Apache Sedona spatial joins, Snowflake ingestion).
- **Module 2 (My Primary Area):** Analytics & Visualization (Commercial zoning preparation, store-level footfall analytics, hourly footfall analytics, dbt transformation models, catchment analysis, cannibalization risk assessment, Kepler.gl dashboard, business insights).
- **Module 3 (Shared Responsibilities):** Apache Airflow DAGs, pipeline integration, end-to-end testing, documentation, final presentation.

---

## 6. Dataset Information (Phase 2 Production Run)

| Dataset | Record Count | File Path | Columns | Processing Status |
|---|---|---|---|---|
| **Raw GPS Mobility** | 25,152 | `data/raw/gps_mobility.csv` | `user_id`, `timestamp`, `latitude`, `longitude`, `accuracy`, `location_id` | Generated (500 users, 501 injected anomalies) |
| **Raw Store Catalog** | 30 | `data/reference/store_locations.csv` | `store_id`, `store_name`, `store_category`, `latitude`, `longitude`, `store_status` | Generated (7 categories, 6 Manhattan retail hubs) |
| **Cleaned GPS Mobility** | 22,991 | `data/processed/cleaned_gps_mobility.csv` | `user_id`, `timestamp`, `latitude`, `longitude`, `accuracy`, `location_id` | Validated, typed, deduplicated |
| **Cleaned Store Catalog** | 30 | `data/processed/cleaned_store_locations.csv` | `store_id`, `store_name`, `store_category`, `latitude`, `longitude`, `store_status` | Validated (100% conforming) |
| **Rejected GPS Records** | 2,161 | `data/rejected/rejected_gps_records.csv` | Raw columns + `rejection_reasons` | Logged (missing user/coords, out of bounds, dupes) |
| **Data Quality Report** | 1 | `data/quality/data_quality_report.json` | Rejection breakdown, input/valid tallies | Status: PASS (8.58% rejection rate) |
| **Nearest Store Mapping** | 22,991 | `data/processed/nearest_store_mapping.csv` | GPS columns + `nearest_store_id`, `distance_km`, `within_distance_threshold` | Mapped (22,988 within 5km threshold, avg 0.135 km) |
| **Detected Store Visits** | 3,487 | `data/processed/detected_store_visits.csv` | `visit_id`, `user_id`, `store_id`, `arrival_time`, `departure_time`, `dwell_time_minutes`, `observation_count`, `min_distance_km`, `visit_date` | Extracted (500 visitors, avg dwell: 22.83 min) |
| **Sedona Spatial Join** | 17,872 | `data/processed/sedona_spatial_results/store_proximity_spatial_join.csv` | Point-in-radius join pairs (distance <= 50m) | Verified consistent with Haversine baseline |

---

## 7. Database Design & Snowflake Integration
- **Database:** `GEOPULSE_DB` (Snowflake)
- **Warehouse:** `GEOPULSE_WH` (X-Small)
- **Schemas Defined:**
  - `RAW`: `RAW.GPS_MOBILITY`, `RAW.STORE_LOCATIONS`
  - `STAGING`: `STAGING.CLEANED_GPS_MOBILITY`, `STAGING.CLEANED_STORE_LOCATIONS`
  - `PROCESSED`: `PROCESSED.NEAREST_STORE_MAPPING`, `PROCESSED.DETECTED_STORE_VISITS`, `PROCESSED.SPATIAL_RESULTS`
  - `ANALYTICS`: Prepared for dbt transformation models.
- **Snowflake Connection Manager:** `snowflake/connection.py`
- **Snowflake Loader:** `snowflake/load_data.py`
  - Pre-upload validation: **100% of local datasets verified READY_FOR_UPLOAD**.
  - Live upload status: **BLOCKED** pending configuration of live Snowflake credentials in `.env`.

---

## 8. Development Progress

### Phase 1: Planning, Requirements, Architecture & Project Foundation
- [x] Project understanding and requirements analysis (Nov 15-17, 2026)
- [x] Functional requirements (`documentation/functional_requirements.md`) (Nov 17, 2026)
- [x] Non-functional requirements (`documentation/non_functional_requirements.md`) (Nov 17, 2026)
- [x] Scope & constraints (`documentation/scope_and_constraints.md`) (Nov 15, 2026)
- [x] System architecture & diagrams (`documentation/system_architecture.md`) (Nov 15, 2026)
- [x] Data flow design (`documentation/data_flow.md`) (Nov 15, 2026)
- [x] Module design (`documentation/module_design.md`) (Nov 15, 2026)
- [x] Database & schema design (`documentation/database_design.md`) (Nov 15, 2026)
- [x] Data dictionary (`documentation/data_dictionary.md`) (Nov 15, 2026)
- [x] Data contracts (`documentation/data_contracts.md`) (Nov 15, 2026)
- [x] Snowflake DDL schema (`documentation/sql/snowflake_schema.sql`) (Nov 15, 2026)
- [x] Repository foundation & directory setup (Nov 17, 2026)
- [x] Dependency specification (`requirements.txt`) (Nov 17, 2026)
- [x] Configuration module (`config/settings.py`, `config/__init__.py`) (Nov 17, 2026)
- [x] Environment variable template (`.env.example`) (Nov 17, 2026)
- [x] User-facing README (`README.md`) (Nov 17, 2026)
- [x] AI Memory File (`AI_README.md`) (Nov 17, 2026)
- [x] Phase 1 Completion Audit: **COMPLETED** (Nov 17, 2026)

### Phase 2: Data Engineering & Spatial Processing
- [x] Phase 1 audit & pending tasks completed (Nov 17, 2026)
- [x] Task 1: Synthetic GPS mobility data generation (`gps_generator.py`) (Nov 17, 2026)
- [x] Task 2: Retail store location generation (`store_generator.py`) (Nov 17, 2026)
- [x] Task 3: Data cleaning & quality validation (`gps_cleaner.py`, `store_cleaner.py`, `data_quality.py`) (Nov 17, 2026)
- [x] Task 4: Haversine distance calculation & nearest-store mapping (`haversine.py`, `nearest_store.py`) (Nov 17, 2026)
- [x] Task 5: Store visit detection engine (`visit_detection.py`) (Nov 17, 2026)
- [x] Task 6: Apache Sedona spatial processor with local GIS fallback (`sedona_processor.py`) (Nov 17, 2026)
- [x] Task 7: Snowflake integration code & DDL schemas (`connection.py`, `load_data.py`, `schemas.sql`) (Nov 17, 2026)
- [x] Unit & integration testing (`tests/`) (Nov 17, 2026)
- [x] Phase 2 completion confirmation: **COMPLETED** (Nov 17, 2026)

---

## 9. Completed Work (Phase 2 Task Summary)

1. **Synthetic GPS Data Generator (`data_engineering/generation/gps_generator.py`):**
   - Implemented `GPSDataGenerator` producing 25,152 observations across 500 users in Manhattan.
   - Incorporated transit walks, store dwell clusters, and 501 injected anomalies (out-of-bounds lat/lon, missing values, duplicates, negative accuracy).
2. **Retail Store Generator (`data_engineering/generation/store_generator.py`):**
   - Implemented `StoreDataGenerator` producing 30 retail stores distributed across 6 retail hubs (Midtown, SoHo, Union Square, Upper East Side, Financial District, Chelsea) with realistic categories and operational statuses.
3. **Data Cleaning & Quality Pipeline (`data_engineering/cleaning/` & `validation/`):**
   - `GPSDataCleaner`: Evaluated 25,152 records, approved 22,991 valid records, rejected 2,161 records (8.59%) with audit reasons saved to `data/rejected/rejected_gps_records.csv`.
   - `StoreDataCleaner`: Validated 30 stores with 100% conformity.
   - `data_quality.py`: Generated consolidated audit report `data/quality/data_quality_report.json` with overall status `PASS`.
4. **Haversine Distance & Nearest Store Mapping (`data_engineering/spatial/`):**
   - `haversine.py`: Vectorized great-circle computation using mean volumetric Earth radius $R = 6371.0088$ km.
   - `nearest_store.py`: Vectorized matrix computation mapped 22,991 points to 30 stores. Average nearest distance: 0.135 km; 22,988 within 5 km threshold.
5. **Store Visit Detection Engine (`data_engineering/spatial/visit_detection.py`):**
   - Filtered 17,750 pings within 50 meters of stores.
   - Grouped consecutive observations per user-store with maximum time gap threshold (30 min) and dwell requirement (5 to 180 min).
   - Extracted 3,487 confirmed visits across 500 users with average dwell of 22.83 minutes.
6. **Apache Sedona & Spatial Processing (`data_engineering/spatial/sedona_processor.py`):**
   - Tested environment; implemented dual-engine architecture supporting Sedona PySpark and high-performance local spatial processing.
   - Spatial join identified 17,872 proximity pairs ($\le 50$ meters) and cross-validated consistency with Haversine baseline.
7. **Snowflake Integration (`snowflake/`):**
   - Authored DDL script `snowflake/schemas.sql` with table definitions across `RAW`, `STAGING`, `PROCESSED`, and `ANALYTICS`.
   - Built `connection.py` and `load_data.py`. Executed pre-upload validation confirming 100% of 7 datasets are valid and ready. Status cleanly marked `BLOCKED` awaiting credentials.
8. **Testing Suite (`tests/`):**
   - Built 7 test modules covering all components.
   - Executed test suite: **13 of 13 tests passed in 0.045s**.

---

## 10. Technical Decisions
1. **Study Area Definition:** Manhattan Urban Core (Lat `[40.7000, 40.8200]`, Lon `[-74.0200, -73.9300]`) with six distinct retail sub-districts.
2. **Haversine Implementation:** Formula vectorized via NumPy matrix broadcasting $((N, 1) \times (1, M))$ computing millions of distance evaluations in under 0.1 seconds.
3. **Visit Identification Protocol:**
   - Spatial threshold: $\le 50$ meters ($0.05$ km).
   - Minimum observations: $\ge 2$ consecutive pings.
   - Dwell duration: $5.0 \le \Delta t \le 180.0$ minutes.
   - Maximum ping gap: 30 minutes (splits visit candidates if user left and returned).
4. **Apache Sedona Engine Architecture:** Dynamic environment detection with automatic fallback to high-performance local spatial join to ensure continuous pipeline execution regardless of local Java/Spark environment.
5. **Snowflake Integration Strategy:** Safe, idempotent loading pattern with pre-flight schema contract validation.

---

## 11. Errors and Solutions
- *Issue:* `pytest` not pre-installed in Python 3.12 environment.
  - *Fix:* Structured all tests with standard library `unittest` (compatible with both `python -m unittest` and `pytest`).
- *Issue:* `python-dotenv` not installed in sandbox environment.
  - *Fix:* Built a zero-dependency `.env` parser fallback inside `config/settings.py`.
- *Issue:* Java runtime absent in sandbox for Apache Sedona.
  - *Fix:* Designed `SedonaSpatialProcessor` with dual-mode execution (Apache Sedona PySpark + local vectorized spatial join), producing identical schema outputs and cross-verifying spatial results against the Haversine baseline.

---

## 12. Testing History

```text
Ran 13 tests in 0.045s
OK
- test_gps_cleaner_filters_invalid_records: PASSED
- test_store_cleaner_validates_categories_and_pks: PASSED
- test_gps_generation_and_anomalies: PASSED
- test_store_generation_schema_and_bounds: PASSED
- test_haversine_vectorized_broadcasting: PASSED
- test_known_distance_empire_to_times_square: PASSED
- test_known_distance_london_to_paris: PASSED
- test_nan_handling: PASSED
- test_zero_distance_same_point: PASSED
- test_nearest_store_selection: PASSED
- test_expected_project_directories_exist: PASSED
- test_spatial_proximity_join: PASSED
- test_visit_detection_within_radius_and_dwell: PASSED
```

---

## 13. Current Status & Next Steps
- **Current Status:** Phase 1 and Phase 2 are **100% COMPLETE**.
- **Next Phase:** Phase 3 — Analytics & Transformations (dbt staging, intermediate, and dimensional marts, commercial zoning preparation, store catchment polygons, catchment overlap analysis, and cannibalization risk scoring).
- **Blockers:** None for local development. Snowflake cloud upload is BLOCKED pending credentials in `.env`, but local data contracts and outputs are fully aligned for dbt models.
