# GeoPulse AI Project Memory

> **Notice:** This file serves as the permanent external memory, development context, and state tracker for AI agents collaborating on the **GeoPulse – Hyper-Local Retail Mobility Analytics** platform. Every AI session MUST read this file before beginning work and update it before completing a session.

---

## 1. Project Overview
- **Project Name:** GeoPulse – Hyper-Local Retail Mobility Analytics
- **Project Objective:** Convert anonymized synthetic GPS mobility streams, retail store locations, and commercial zoning geometries into actionable business insights regarding footfall, catchment basins, territory overlap, and cannibalization.
- **Business Problem:** Retailers lack transparent, hyper-local intelligence to measure true store catchment boundaries, understand visitor dwell behavior, prevent self-cannibalization between nearby franchise stores, and identify high-potential expansion zones.
- **Target Users:** Retail portfolio strategists, franchise planners, commercial real estate developers, and marketing analysts.
- **Expected Outcomes:** Cleaned mobility datasets, Haversine nearest-store proximity mapping, visit candidate dwell detection, commercial zoning point-in-polygon containment, dbt analytical marts, and interactive Kepler.gl dashboards.

---

## 2. Technology Stack

| Technology | Purpose | Module | Version / Target |
|---|---|---|---|
| **Python** | Primary development language & pipeline logic | Cross-Module | 3.12 (via codex runtime) |
| **Pandas** | Tabular cleaning, manipulation, and transformations | Module 1 & 2 | 3.0.1 |
| **NumPy** | Vectorized mathematical operations & Haversine | Module 1 | 2.3.5 |
| **Haversine** | Great-circle geographic distance calculations | Module 1 | Custom vectorized engine |
| **Spatial / Geodesic Engine** | Geodesic polygon area ($km^2$), ray-casting point-in-polygon | Module 2 | Custom spherical excess engine |
| **Apache Sedona / Spatial Engine** | Spatial joins, point geometry & radius joins | Module 1 | Dual-mode: Sedona ready + Local Fallback |
| **Snowflake** | Cloud Data Warehouse (RAW, STAGING, PROCESSED, ANALYTICS) | Module 1 & 2 | DDL schemas & loaders ready |
| **dbt (dbt-snowflake)** | In-warehouse SQL transformations (Staging, Int, Marts) | Module 2 | 14 ANSI models + local execution runner |
| **Kepler.gl** | WebGL geospatial map rendering | Module 2 | Ready for Phase 4 |
| **Plotly** | Time-series, hourly distribution & footfall metrics | Module 2 | Ready for Phase 4 |
| **unittest / pytest** | Automated test suite | Module 3 | 23/23 passing tests (100% pass rate) |

---

## 3. Project Architecture
The platform operates on an **8-Layer Architecture**:
1. **Data Source Layer:** Synthetic GPS mobility (`data/raw/gps_mobility.csv`), retail store locations (`data/reference/store_locations.csv`), commercial zones (`data/reference/commercial_zones.csv`).
2. **Data Engineering Layer:** `data_engineering/cleaning/gps_cleaner.py` and `store_cleaner.py` routing invalid rows to `data/rejected/`.
3. **Spatial Processing Layer:** Vectorized Haversine distance (`data_engineering/spatial/haversine.py`), nearest-store mapping (`nearest_store.py`), visit dwell time detection (`visit_detection.py`), Apache Sedona / spatial join engine (`sedona_processor.py`).
4. **Commercial Zoning Layer:** Point-in-polygon spatial containment join (`analytics/commercial_zoning/store_zone_mapping.py`), visit-to-zone mapping (`visit_zone_mapping.py`), and zone vitality summarization (`zone_summary.py`).
5. **Data Warehouse Layer:** Snowflake (`GEOPULSE_DB`) schemas: `RAW`, `STAGING`, `PROCESSED`, and `ANALYTICS`. Connection and loaders in `snowflake/`.
6. **dbt Transformation Layer:** 14 models structured as `staging/` (standardize/typecast), `intermediate/` (enrich/time dimensions), and `marts/` (business marts: store footfall, hourly patterns, daily performance, zone vitality, scorecards).
7. **Dashboard Layer:** Kepler.gl interactive map views + Plotly analytical charts (Phase 4).
8. **Orchestration Layer:** Apache Airflow DAGs triggering generation, cleaning, loading, and dbt runs (Phase 4).

---

## 4. Repository Structure

```text
c:\Users\yash\geoplus\
├── data/
│   ├── raw/                  # gps_mobility.csv (25,152 rows), gps_generation_summary.json
│   ├── reference/            # store_locations.csv (30 stores), commercial_zones.csv (6 zones), commercial_zones.geojson
│   ├── processed/            # cleaned_gps_mobility.csv (22,991 rows), cleaned_store_locations.csv (30 rows),
│   │                         # nearest_store_mapping.csv (22,991 rows), detected_store_visits.csv (3,487 rows),
│   │                         # store_zone_mapping.csv (30 rows), visit_zone_mapping.csv (3,487 rows),
│   │                         # commercial_zone_summary.csv (6 zones),
│   │                         # sedona_spatial_results/ (spatially_enriched_gps.csv, store_proximity_spatial_join.csv),
│   │                         # marts/ (mart_store_footfall.csv, mart_hourly_footfall.csv, mart_daily_footfall.csv,
│   │                         #        mart_zone_footfall.csv, mart_store_performance.csv)
│   ├── rejected/             # rejected_gps_records.csv (2,161 rows), rejected_store_records.csv (0 rows)
│   └── quality/              # data_quality_report.json
├── data_engineering/
│   ├── generation/           # gps_generator.py, store_generator.py
│   ├── cleaning/             # gps_cleaner.py, store_cleaner.py
│   ├── spatial/              # haversine.py, nearest_store.py, visit_detection.py, sedona_processor.py
│   └── validation/           # data_quality.py
├── analytics/
│   └── commercial_zoning/    # zone_generator.py, zone_validator.py, store_zone_mapping.py,
│                             # visit_zone_mapping.py, zone_summary.py
├── dbt_geopulse/
│   ├── dbt_project.yml       # dbt project configuration
│   ├── profiles.yml.example  # connection profile template
│   ├── local_runner.py       # local SQL execution & test verification runner
│   ├── models/
│   │   ├── staging/          # stg_gps_mobility.sql, stg_store_locations.sql, stg_store_visits.sql,
│   │   │                     # stg_commercial_zones.sql, stg_store_zone_mapping.sql, staging.yml
│   │   ├── intermediate/     # int_valid_store_visits.sql, int_visit_time_dimensions.sql,
│   │   │                     # int_visit_zone_mapping.sql, int_store_footfall_base.sql, intermediate.yml
│   │   └── marts/            # mart_store_footfall.sql, mart_hourly_footfall.sql, mart_daily_footfall.sql,
│   │                         # mart_zone_footfall.sql, mart_store_performance.sql, marts.yml
│   └── tests/                # assert_no_future_visits.sql, assert_positive_dwell_time.sql,
│                             # assert_valid_store_references.sql, assert_visit_grain_uniqueness.sql
├── snowflake/                # connection.py, load_data.py, schemas.sql
├── tests/                    # test_cleaning.py, test_generation.py, test_haversine.py, test_nearest_store.py,
│                             # test_visit_detection.py, test_sedona.py, test_project_scaffold.py,
│                             # test_commercial_zoning.py, test_dbt_analytics.py
├── documentation/            # project_overview.md, functional_requirements.md, non_functional_requirements.md,
│                             # system_architecture.md, data_flow.md, module_design.md, database_design.md,
│                             # data_dictionary.md, data_contracts.md, scope_and_constraints.md,
│                             # phase2_audit.md, commercial_zoning.md, dbt_architecture.md,
│                             # analytics_metrics.md, phase3_report.md
├── config/                   # settings.py, __init__.py
├── README.md                 # Developer & user documentation
└── AI_README.md              # AI Project Memory
```

---

## 5. Phase 2 Completion Audit Results
- **GPS Data Generation:** 25,152 observations generated across 500 users with 501 injected anomalies. Status: **COMPLETED**.
- **Store Data Generation:** 30 retail stores generated across 6 Manhattan retail clusters. Status: **COMPLETED**.
- **Data Cleaning & Validation:** 22,991 clean records, 2,161 rejected pings with audit reasons. Status: **COMPLETED**.
- **Haversine & Nearest Store:** 22,991 mapped (avg distance 0.135 km; 22,988 within 5 km threshold). Status: **COMPLETED**.
- **Store Visit Detection:** 3,487 confirmed visits (radius $\le 50$m, dwell $5$–$180$m). Status: **COMPLETED**.
- **Sedona Spatial Processing:** 17,872 proximity pairs matched ($\le 50$m); consistency verified with Haversine. Status: **COMPLETED**.
- **Snowflake Integration:** All 7 datasets validated `READY_FOR_UPLOAD`; upload status `BLOCKED` awaiting credentials. Status: **BLOCKED (Documented)**.
- **Audit Report:** Officially recorded in `documentation/phase2_audit.md`. Overall Phase 2 status: **100% COMPLETE**.

---

## 6. Phase 3 Development Progress

- [x] Phase 2 audit & documentation (`documentation/phase2_audit.md`) (Nov 25, 2026)
- [x] Commercial zone generation (`zone_generator.py`) (Nov 25, 2026)
- [x] Zone geometry validation & geodesic area calculation (`zone_validator.py`) (Nov 25, 2026)
- [x] Store-to-zone spatial point-in-polygon mapping (`store_zone_mapping.py`) (Nov 25, 2026)
- [x] Visit-to-zone mapping preserving strict visit grain (`visit_zone_mapping.py`) (Nov 25, 2026)
- [x] Commercial zone summary compilation (`zone_summary.py`) (Nov 25, 2026)
- [x] dbt project configuration (`dbt_project.yml`, `profiles.yml.example`) (Nov 25, 2026)
- [x] Staging models (`stg_gps_mobility`, `stg_store_locations`, `stg_store_visits`, `stg_commercial_zones`, `stg_store_zone_mapping`, `staging.yml`) (Nov 25, 2026)
- [x] Intermediate models (`int_valid_store_visits`, `int_visit_time_dimensions`, `int_visit_zone_mapping`, `int_store_footfall_base`, `intermediate.yml`) (Nov 25, 2026)
- [x] Store-level footfall analytics (`mart_store_footfall.sql`) (Nov 25, 2026)
- [x] Hourly footfall analytics (`mart_hourly_footfall.sql`) (Nov 25, 2026)
- [x] Daily footfall analytics (`mart_daily_footfall.sql`) (Nov 25, 2026)
- [x] Commercial zone analytics (`mart_zone_footfall.sql`) (Nov 25, 2026)
- [x] Store performance scorecard (`mart_store_performance.sql`, `marts.yml`) (Nov 25, 2026)
- [x] Custom dbt tests (`assert_no_future_visits`, `assert_positive_dwell_time`, `assert_valid_store_references`, `assert_visit_grain_uniqueness`) (Nov 25, 2026)
- [x] Local dbt execution engine & test runner (`dbt_geopulse/local_runner.py`) (Nov 25, 2026)
- [x] Automated test suite execution (`test_commercial_zoning.py`, `test_dbt_analytics.py`: 23/23 tests passed) (Nov 25, 2026)
- [x] Phase 3 documentation (`commercial_zoning.md`, `dbt_architecture.md`, `analytics_metrics.md`, `phase3_report.md`) (Nov 25, 2026)
- [x] Phase 3 Status Confirmation: **COMPLETED** (Nov 25, 2026)

---

## 7. Dataset Information (Phase 3 Production Run)

| Dataset | Record Count | File Path | Grain / Entity | Processing Status |
|---|---|---|---|---|
| **Commercial Zones (CSV)** | 6 | `data/reference/commercial_zones.csv` | Commercial Zone (`zone_id`) | Generated with WKT geometries & geodesic areas |
| **Commercial Zones (GeoJSON)** | 6 | `data/reference/commercial_zones.geojson` | GeoJSON FeatureCollection | Validated polygon features |
| **Store-Zone Mapping** | 30 | `data/processed/store_zone_mapping.csv` | Store (`store_id`) | 20 inside zones, 10 peripheral unzoned |
| **Visit-Zone Mapping** | 3,487 | `data/processed/visit_zone_mapping.csv` | Visit event (`visit_id`) | 2,321 in zones, 1,166 unzoned; 1-to-1 visit grain |
| **Commercial Zone Summary** | 6 | `data/processed/commercial_zone_summary.csv` | Zone (`zone_id`) | Summarized by total visits, unique patrons, dwell |
| **Mart: Store Footfall** | 26 | `data/processed/marts/mart_store_footfall.csv` | Store (`store_id`) | Ranked by footfall, unique patrons, repeat % |
| **Mart: Hourly Footfall** | 413 | `data/processed/marts/mart_hourly_footfall.csv` | Store-Date-Hour | Hourly traffic share %, peak hour identified |
| **Mart: Daily Footfall** | 26 | `data/processed/marts/mart_daily_footfall.csv` | Store-Date | Day-of-week trends vs store baseline |
| **Mart: Zone Footfall** | 6 | `data/processed/marts/mart_zone_footfall.csv` | Zone (`zone_id`) | Zone vitality rank, visits per $km^2$ |
| **Mart: Store Performance** | 26 | `data/processed/marts/mart_store_performance.csv` | Store (`store_id`) | Volume, peak hour, repeat rate, weekend lift ratio |

---

## 8. dbt Model Registry & Execution Metrics

| Model Name | Layer | Materialization | Input Sources / Refs | Output Rows | Primary Key / Grain | Tests Passed |
|---|---|---|---|---|---|---|
| `stg_gps_mobility` | Staging | View | `raw.raw_gps_mobility` | 24,793 | Observation | not_null |
| `stg_store_locations` | Staging | View | `raw.raw_store_locations` | 30 | `store_id` | unique, not_null, accepted_values |
| `stg_store_visits` | Staging | View | `processed.detected_store_visits` | 3,487 | `visit_id` | unique, not_null, positive dwell |
| `stg_commercial_zones` | Staging | View | `reference.commercial_zones` | 6 | `zone_id` | unique, not_null |
| `stg_store_zone_mapping` | Staging | View | `processed.store_zone_mapping` | 30 | `store_id` | unique, not_null |
| `int_valid_store_visits` | Intermediate | Table | `stg_store_visits`, `stg_store_locations` | 3,487 | `visit_id` | unique, not_null, active stores only |
| `int_visit_time_dimensions`| Intermediate | Table | `int_valid_store_visits` | 3,487 | `visit_id` | unique, not_null, dayparts |
| `int_visit_zone_mapping` | Intermediate | Table | `int_visit_time_dimensions`, `stg_store_zone_mapping` | 3,487 | `visit_id` | unique, not_null, 1-to-1 visit grain |
| `int_store_footfall_base` | Intermediate | Table | `int_visit_time_dimensions` | 26 | `store_id`, `visit_date` | not_null |
| `mart_store_footfall` | Marts | Table | `int_visit_zone_mapping`, `int_store_footfall_base` | 26 | `store_id` | unique, not_null, rank |
| `mart_hourly_footfall` | Marts | Table | `int_visit_time_dimensions` | 413 | `store_id`, `date`, `hour` | not_null, peak hour flag |
| `mart_daily_footfall` | Marts | Table | `int_store_footfall_base` | 26 | `store_id`, `visit_date` | not_null, weekend ratio |
| `mart_zone_footfall` | Marts | Table | `int_visit_zone_mapping`, `stg_commercial_zones` | 6 | `zone_id` | unique, not_null, density |
| `mart_store_performance` | Marts | Table | `int_visit_zone_mapping` | 26 | `store_id` | unique, not_null, weekend lift |

---

## 9. Commercial Zoning Summary

| Zone ID | Zone Name | Zone Type | Area ($km^2$) | Stores | Total Visits | Unique Patrons | Avg Dwell (min) | Top Category | Daily Footfall | Density (Visits/$km^2$) |
|---|---|---|---|---|---|---|---|---|---|---|
| `ZN_001` | Midtown / Herald Square | Shopping District | 0.98 | 5 | 684 | 366 | 23.02 | Cafe & Bakery | 85.50 | 698.81 |
| `ZN_003` | Union Sq / Flatiron | Mixed Commercial | 1.03 | 6 | 674 | 379 | 23.12 | Convenience | 84.25 | 654.05 |
| `ZN_005` | Upper East Side | Retail Complex | 1.34 | 5 | 544 | 332 | 22.43 | Dept Store | 68.00 | 406.27 |
| `ZN_002` | SoHo Historic Corridor | Main Market | 1.03 | 3 | 285 | 219 | 22.58 | Pharmacy | 35.62 | 276.48 |
| `ZN_004` | Financial District | Business District | 1.01 | 1 | 134 | 117 | 22.81 | Cafe & Bakery | 16.75 | 132.38 |
| `ZN_006` | Chelsea / Meatpacking | Local Market | 1.12 | 0 | 0 | 0 | 0.00 | N/A | 0.00 | 0.00 |

---

## 10. Technical Decisions
1. **Geodesic Surface Area Calculation:** Used spherical excess integration with mean Earth radius $R = 6371.0088$ km rather than planar degree-squared approximations, ensuring geometric fidelity.
2. **Strict Visit Grain Conservation:** Enforced a left join on store mapping with validation ensuring that $|V_{\text{mapped}}| = |V_{\text{detected}}| = 3,487$. Zero visits are dropped or multiplied during zone assignment.
3. **Dual Execution Architecture for dbt:** Authored ANSI-compliant SQL models with Jinja templating suitable for Snowflake, coupled with a local SQL runner (`dbt_geopulse/local_runner.py`) using in-memory execution to certify transformations and produce actual output marts locally.
4. **Repeat Visitor Formulation:** Derived customer loyalty via $\frac{\text{Visits} - \text{Unique Patrons}}{\text{Visits}} \times 100\%$, indicating retention without conflating single-day pings.
5. **Weekend Lift Normalization:** Normalized weekend vs. weekday traffic across 2 weekend days vs. 5 weekdays to avoid skewed 5:2 day-count artifacts.

---

## 11. Errors and Solutions
- *Error:* `sqlite3.OperationalError: no such function: GREATEST` encountered in `mart_zone_footfall.sql` during local runner execution.
  - *Solution:* Replaced `GREATEST(...)` with ANSI standard `CASE WHEN ... > ... THEN ... ELSE ... END` and registered `GREATEST` as an in-memory SQL function in `local_runner.py`.
- *Deprecation Notice:* `datetime.datetime.utcnow()` deprecation in Python 3.12.
  - *Solution:* Standardized on ISO UTC string formatting across data generation and runner scripts.

---

## 12. Testing History

```text
Ran 23 tests in 0.347s
OK (100% Pass Rate)

Phase 2 Tests (13 tests):
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

Phase 3 Commercial Zoning Tests (5 tests):
- test_geodesic_polygon_area_calculation: PASSED
- test_point_in_polygon_containment: PASSED
- test_store_zone_mapping_preserves_unmatched: PASSED
- test_visit_zone_mapping_strict_grain: PASSED
- test_zone_generator_and_validator: PASSED

Phase 3 dbt Analytics Integration Tests (5 tests):
- test_all_models_execute_successfully: PASSED (14 models)
- test_dbt_custom_assertions_pass: PASSED (4 custom tests, 0 failures)
- test_mart_store_footfall_grain_and_metrics: PASSED
- test_mart_store_performance_rankings: PASSED
- test_mart_zone_footfall_conservation: PASSED
```

---

## 13. Current Status & Next Steps
- **Current Status:** Phase 1, Phase 2, and Phase 3 are **100% COMPLETE**.
- **Next Phase:** Phase 4 — Store Catchment Delineation, Spatial Overlap & Cannibalization Risk Assessment, Kepler.gl Geospatial Dashboard, and Apache Airflow Orchestration.
- **Git Branch:** Clean working tree on `Kamal-Geopulse`.
