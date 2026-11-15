# GeoPulse — Data Flow Specification

> **Version:** 1.0  
> **Date:** 2026-11-15  
> **Status:** Day 2 — Architecture & Data Flow Design  

---

## 1. End-to-End Data Flow Description

The GeoPulse pipeline transforms **synthetic GPS mobility data** into **actionable retail analytics** through six sequential stages:

1. **Generation:** Python scripts produce ~250,000 synthetic GPS pings for ~5,000 simulated users moving through a metropolitan area over a configurable date range. Concurrently, ~75 retail store locations and ~15 commercial zone polygons are generated. All raw files land in `data/raw/`.

2. **Cleaning & Validation:** Raw datasets pass through the data quality layer. GPS pings are deduplicated, coordinates validated (latitude ∈ [−90, 90], longitude ∈ [−180, 180]), timestamps parsed and normalized to UTC, and null values handled. Stores are validated for unique IDs and valid coordinates. Zones are checked for valid GeoJSON polygon geometry. Cleaned outputs land in `data/processed/`.

3. **Spatial Enrichment:** The Haversine formula calculates the distance from each GPS ping to every store, and each ping is assigned to its nearest store (within a configurable radius threshold, e.g. 500 m). Apache Sedona performs spatial joins — point-in-polygon operations assign each ping to a commercial zone. The result is a spatially enriched visit dataset.

4. **Warehouse Loading:** Enriched datasets are loaded into Snowflake's `RAW` schema via staged file uploads (`PUT` + `COPY INTO`). This is the boundary where on-disk files transition to cloud-hosted SQL tables.

5. **dbt Transformation:** dbt models progressively transform data through `STAGING` (type-cast, rename), `INTERMEDIATE` (aggregate, join), and `MARTS` (business-ready) schemas. Mart tables contain store-level daily footfall, hourly footfall patterns, catchment area metrics, store overlap matrices, and cannibalization risk scores.

6. **Analytics & Visualization:** Python analytics scripts query the mart tables (or consume exported files) to produce business insights. Kepler.gl renders geospatial maps (store catchment areas, heatmaps of foot traffic). Plotly generates interactive charts (hourly footfall trends, cannibalization bar charts). Final outputs are saved to `reports/` and `dashboard/`.

---

## 2. Pipeline Flow Diagrams

### 2a. Overall Pipeline Flow — High-Level End-to-End

```mermaid
flowchart TD
    A["1. Data Generation<br/>GPS, Stores, Zones"] -->|data/raw/| B["2. Data Cleaning & Validation"]
    B -->|data/processed/| C["3. Spatial Processing<br/>Haversine + Sedona"]
    C -->|data/processed/| D["4. Snowflake Loading<br/>RAW Schema"]
    D -->|SQL| E["5. dbt Transformations<br/>STAGING → INTERMEDIATE → MARTS"]
    E -->|MARTS tables| F["6. Analytics Engine<br/>Footfall, Catchment, Overlap"]
    F -->|data/analytics/| G["7. Dashboard & Reports<br/>Kepler.gl + Plotly"]

    style A fill:#4CAF50,color:#fff
    style B fill:#2196F3,color:#fff
    style C fill:#FF9800,color:#fff
    style D fill:#9C27B0,color:#fff
    style E fill:#F44336,color:#fff
    style F fill:#00BCD4,color:#fff
    style G fill:#795548,color:#fff
```

---

### 2b. Data Engineering Sub-flow

*Module 1 responsibility — from generation through to Snowflake RAW.*

```mermaid
flowchart TD
    subgraph Generation["Step 1: Data Generation"]
        G1["gps_generator.py<br/>~250K pings"]
        G2["store_generator.py<br/>~75 stores"]
        G3["zone_generator.py<br/>~15 zones"]
    end

    subgraph Cleaning["Step 2: Data Cleaning"]
        C1["Deduplicate GPS pings"]
        C2["Validate coordinates"]
        C3["Parse timestamps → UTC"]
        C4["Null handling & type casting"]
        C5["GeoJSON geometry validation"]
    end

    subgraph Spatial["Step 3: Spatial Processing"]
        S1["Haversine distance calc<br/>ping ↔ all stores"]
        S2["Nearest-store assignment<br/>within 500m radius"]
        S3["Sedona: point-in-polygon<br/>ping → zone"]
        S4["Spatial join output<br/>enriched visits"]
    end

    subgraph Loading["Step 4: Snowflake Loading"]
        L1["Stage files via PUT"]
        L2["COPY INTO raw_gps_pings"]
        L3["COPY INTO raw_retail_stores"]
        L4["COPY INTO raw_commercial_zones"]
    end

    G1 -->|gps_pings.csv| C1
    G2 -->|retail_stores.csv| C2
    G3 -->|commercial_zones.geojson| C5

    C1 --> C3 --> C4
    C2 --> C4

    C4 -->|gps_pings_clean.csv| S1
    C4 -->|retail_stores_clean.csv| S1
    C5 -->|zones_clean.geojson| S3

    S1 --> S2
    S2 --> S4
    S3 --> S4

    S4 -->|enriched files| L1
    L1 --> L2
    L1 --> L3
    L1 --> L4
```

---

### 2c. Analytics Sub-flow

*Module 2 responsibility — from Snowflake through dbt to dashboards.*

```mermaid
flowchart TD
    subgraph Sources["Snowflake RAW"]
        R1["raw_gps_pings"]
        R2["raw_retail_stores"]
        R3["raw_commercial_zones"]
    end

    subgraph DBT_Staging["dbt staging/"]
        S1["stg_gps__pings<br/>Type-cast, deduplicate"]
        S2["stg_stores__locations<br/>Validate, rename"]
        S3["stg_zones__boundaries<br/>Parse geometry"]
    end

    subgraph DBT_Intermediate["dbt intermediate/"]
        I1["int_visits__store_assignments<br/>Join pings ↔ nearest store"]
        I2["int_footfall__hourly_counts<br/>COUNT by store × hour"]
        I3["int_footfall__store_daily<br/>COUNT by store × day"]
        I4["int_catchment__zone_mapping<br/>Map stores → zones"]
    end

    subgraph DBT_Marts["dbt marts/"]
        M1["mart_footfall__store_daily"]
        M2["mart_footfall__hourly_pattern"]
        M3["mart_catchment__store_areas"]
        M4["mart_catchment__overlap_matrix"]
        M5["mart_cannibalization__risk_scores"]
    end

    subgraph Analytics["Python Analytics"]
        A1["footfall_analyzer.py"]
        A2["hourly_analyzer.py"]
        A3["catchment_analyzer.py"]
        A4["overlap_detector.py"]
        A5["cannibalization_assessor.py"]
    end

    subgraph Dashboards["Visualization"]
        D1["Kepler.gl Maps<br/>Catchment, heatmaps"]
        D2["Plotly Charts<br/>Trends, bar charts"]
        D3["Business Reports<br/>PDF / HTML"]
    end

    R1 --> S1
    R2 --> S2
    R3 --> S3

    S1 --> I1
    S2 --> I1
    S1 --> I2
    I1 --> I3
    S3 --> I4
    S2 --> I4

    I3 --> M1
    I2 --> M2
    I4 --> M3
    M3 --> M4
    M4 --> M5

    M1 --> A1
    M2 --> A2
    M3 --> A3
    M4 --> A4
    M5 --> A5

    A1 --> D1
    A1 --> D2
    A2 --> D2
    A3 --> D1
    A4 --> D2
    A5 --> D3
```

---

### 2d. Airflow Orchestration — DAG Structure

*Module 3 (shared) — task dependency graph within the Airflow DAG.*

```mermaid
flowchart TD
    START(["DAG Start<br/>geopulse_pipeline"]) --> GEN_GPS["generate_gps_data"]
    START --> GEN_STORES["generate_store_data"]
    START --> GEN_ZONES["generate_zone_data"]

    GEN_GPS --> CLEAN["clean_and_validate"]
    GEN_STORES --> CLEAN
    GEN_ZONES --> CLEAN

    CLEAN --> HAVERSINE["calculate_haversine_distances"]
    CLEAN --> SEDONA["run_sedona_spatial_joins"]

    HAVERSINE --> NEAREST["assign_nearest_stores"]
    NEAREST --> MERGE["merge_spatial_results"]
    SEDONA --> MERGE

    MERGE --> LOAD_SF["load_to_snowflake_raw"]

    LOAD_SF --> DBT_STAGING["dbt_run_staging"]
    DBT_STAGING --> DBT_TEST_STG["dbt_test_staging"]
    DBT_TEST_STG --> DBT_INTERMEDIATE["dbt_run_intermediate"]
    DBT_INTERMEDIATE --> DBT_TEST_INT["dbt_test_intermediate"]
    DBT_TEST_INT --> DBT_MARTS["dbt_run_marts"]
    DBT_MARTS --> DBT_TEST_MRT["dbt_test_marts"]

    DBT_TEST_MRT --> ANALYTICS_FOOTFALL["run_footfall_analytics"]
    DBT_TEST_MRT --> ANALYTICS_HOURLY["run_hourly_analytics"]
    DBT_TEST_MRT --> ANALYTICS_CATCHMENT["run_catchment_analytics"]

    ANALYTICS_CATCHMENT --> ANALYTICS_OVERLAP["run_overlap_detection"]
    ANALYTICS_OVERLAP --> ANALYTICS_CANNIBAL["run_cannibalization_assessment"]

    ANALYTICS_FOOTFALL --> DASHBOARD["build_dashboard"]
    ANALYTICS_HOURLY --> DASHBOARD
    ANALYTICS_CANNIBAL --> DASHBOARD

    DASHBOARD --> REPORT["generate_reports"]
    REPORT --> END_(["DAG End"])

    style START fill:#4CAF50,color:#fff
    style END_ fill:#4CAF50,color:#fff
    style LOAD_SF fill:#9C27B0,color:#fff
    style DBT_STAGING fill:#F44336,color:#fff
    style DBT_INTERMEDIATE fill:#F44336,color:#fff
    style DBT_MARTS fill:#F44336,color:#fff
```

---

## 3. Data Transformation Rules

### Stage-by-Stage Transformations

| Stage | Transformation Rules |
|---|---|
| **Raw → Cleaned** | • Remove exact-duplicate rows<br>• Validate latitude ∈ [−90, 90], longitude ∈ [−180, 180]; drop or flag out-of-bounds<br>• Parse `ping_timestamp` string → `datetime` (UTC)<br>• Fill missing `user_id` → drop row (no imputation for identifiers)<br>• Ensure `store_id` uniqueness<br>• Validate GeoJSON `type == "Polygon"` and ring closure |
| **Cleaned → Spatially Enriched** | • Compute Haversine distance (km) from each ping to each store<br>• Assign `nearest_store_id` = store with minimum distance where distance ≤ 0.5 km<br>• Pings with no store within threshold → `nearest_store_id = NULL` (excluded from footfall)<br>• Sedona spatial join: assign `zone_id` from polygon containment |
| **RAW → STAGING (dbt)** | • `CAST` all columns to proper types (`VARCHAR` → `FLOAT`, `TIMESTAMP`, `INTEGER`)<br>• Rename columns to snake_case convention<br>• Deduplicate via `ROW_NUMBER() OVER (PARTITION BY ping_id ORDER BY loaded_at DESC)`<br>• Add `_loaded_at` audit column |
| **STAGING → INTERMEDIATE (dbt)** | • `JOIN` pings with stores on `nearest_store_id`<br>• `GROUP BY store_id, DATE_TRUNC('day', visit_time)` → daily footfall<br>• `GROUP BY store_id, HOUR(visit_time)` → hourly footfall<br>• `JOIN` stores with zones on spatial containment |
| **INTERMEDIATE → MARTS (dbt)** | • Add store metadata (name, address, zone) to footfall tables<br>• Compute catchment area metrics (unique visitors, visit frequency, avg dwell proxy)<br>• Build pairwise overlap matrix: `shared_visitors / LEAST(visitors_a, visitors_b)`<br>• Calculate cannibalization score: weighted combination of overlap %, distance, zone co-location |

---

## 4. Data Volume Estimates

| Dataset | Estimated Volume | Row Size (approx.) | Storage (approx.) |
|---|---|---|---|
| **GPS Pings (raw)** | ~250,000 rows | ~100 bytes/row | ~25 MB |
| **Unique Users** | ~5,000 | — | — |
| **Retail Stores** | ~75 rows | ~200 bytes/row | <1 MB |
| **Commercial Zones** | ~15 rows | ~2 KB/row (GeoJSON) | <1 MB |
| **Cleaned GPS Pings** | ~237,500 (after ~5% drop) | ~120 bytes/row | ~28 MB |
| **Nearest-Store Assignments** | ~237,500 | ~140 bytes/row | ~33 MB |
| **Processed Visits** | ~50,000–100,000 | ~160 bytes/row | ~16 MB |
| **Store Daily Footfall (mart)** | ~75 stores × ~30 days = ~2,250 | ~80 bytes/row | <1 MB |
| **Hourly Footfall (mart)** | ~75 × 24 = ~1,800 | ~60 bytes/row | <1 MB |
| **Overlap Matrix** | ~75 × 75 / 2 = ~2,812 pairs | ~50 bytes/row | <1 MB |
| **Cannibalization Scores** | ~75 stores | ~100 bytes/row | <1 MB |

> [!NOTE]
> Total pipeline data footprint is well under 100 MB. Snowflake micro-partitioning and clustering are not critical at this scale but may be configured for demonstration purposes.

---

## 5. Processing Dependencies

The following dependency graph defines what must complete before what. Any violation causes pipeline failure.

```mermaid
flowchart TD
    A["GPS Generation"] --> D["Data Cleaning"]
    B["Store Generation"] --> D
    C["Zone Generation"] --> D

    D --> E["Haversine Calculation"]
    D --> F["Sedona Spatial Joins"]

    E --> G["Nearest-Store Mapping"]
    G --> H["Merge Spatial Results"]
    F --> H

    H --> I["Snowflake RAW Loading"]

    I --> J["dbt staging"]
    J --> K["dbt intermediate"]
    K --> L["dbt marts"]

    L --> M["Footfall Analytics"]
    L --> N["Hourly Analytics"]
    L --> O["Catchment Analytics"]

    O --> P["Overlap Detection"]
    P --> Q["Cannibalization Assessment"]

    M --> R["Dashboard Build"]
    N --> R
    Q --> R

    R --> S["Report Generation"]
```

### Critical Path

The longest sequential chain determines minimum pipeline runtime:

```
GPS Generation → Cleaning → Haversine → Nearest-Store → Merge → Snowflake Load
  → dbt staging → dbt intermediate → dbt marts → Catchment Analytics
  → Overlap Detection → Cannibalization Assessment → Dashboard → Report
```

### Parallelization Opportunities

| Step | Can Run In Parallel With |
|---|---|
| GPS Generation | Store Generation, Zone Generation |
| Haversine Calculation | Sedona Spatial Joins |
| Footfall Analytics | Hourly Analytics, Catchment Analytics |
| Kepler.gl Map Build | Plotly Chart Generation |

---

## 6. Error Handling Strategy

### Layer-by-Layer Error Handling

| Layer | Error Type | Handling Strategy | Recovery |
|---|---|---|---|
| **Data Generation** | Config errors (invalid params) | Raise `ValueError` with descriptive message; fail fast | Fix config and re-run |
| **Data Generation** | File I/O errors | Catch `IOError`; log and retry once; fail if persists | Check disk space/permissions |
| **Data Cleaning** | Invalid coordinates | Log warning with row index; drop row; track count in quality report | Review quality report; adjust generator if drop rate > 10% |
| **Data Cleaning** | Null identifiers (`user_id`, `store_id`) | Drop row; log to `data/logs/cleaning_dropped.csv` | Investigate generator |
| **Data Cleaning** | Timestamp parse failures | Attempt multiple formats (`ISO 8601`, `Unix epoch`); drop if all fail | Fix generator output format |
| **Spatial Processing** | No store within radius threshold | Set `nearest_store_id = NULL`; exclude from footfall counts | Adjust radius or store density |
| **Spatial Processing** | Sedona geometry errors | Catch `GeoException`; log invalid geometries; skip affected rows | Fix zone GeoJSON |
| **Snowflake Loading** | Connection failure | Retry with exponential backoff (3 attempts, 5s/15s/45s delay) | Check credentials in `.env` |
| **Snowflake Loading** | COPY INTO partial failure | Log rejected rows via Snowflake `VALIDATION_MODE`; load accepted rows | Review rejected row log |
| **dbt Transformation** | Test failure (schema, data) | dbt stops downstream models; Airflow task fails | Fix source data or model logic; `dbt retry` |
| **dbt Transformation** | Model compilation error | dbt exits with error code; Airflow marks task failed | Fix SQL / Jinja syntax |
| **Analytics** | Empty input data | Check row count before processing; raise `DataError` if zero | Verify upstream dbt models ran |
| **Analytics** | Division by zero (metrics) | Use safe division: `NULLIF(denominator, 0)` or `np.where` guards | Review metric formulas |
| **Dashboard** | Kepler.gl config mismatch | Validate config schema before render; fallback to default config | Regenerate config from data |
| **Airflow** | Task failure | Retry up to 2 times with 5-minute delay; alert on final failure | Check logs; fix and trigger task re-run |
| **Airflow** | DAG timeout | Set `dagrun_timeout`; alert on breach | Investigate bottleneck; optimize |

### Logging & Observability

- **Python scripts:** Use `logging` module with `INFO`/`WARNING`/`ERROR` levels. Log to both console and `data/logs/<script>_<date>.log`.
- **dbt:** Built-in logging to `dbt/logs/`. Use `dbt test` for data quality assertions.
- **Airflow:** Native task logs in Airflow UI. Configure email alerts on task failure.
- **Quality Reports:** Each pipeline run produces a `data/logs/quality_report.json` summarizing rows in, rows dropped, and drop reasons per stage.

### Circuit Breaker Pattern

If the data cleaning stage drops more than **15%** of GPS pings, the pipeline halts and raises an alert rather than propagating suspicious data downstream. This threshold is configurable via environment variable `GEOPULSE_MAX_DROP_RATE`.
