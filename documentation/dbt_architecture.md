# GeoPulse — dbt Analytics Architecture & Data Lineage

> **Document**: dbt Analytics Architecture Specification  
> **Project**: GeoPulse — Hyper-Local Retail Mobility Analytics  
> **Phase**: Phase 3  
> **Last Updated**: 2026-11-25  

---

## 1. Architectural Philosophy

GeoPulse adopts the **Medallion / 3-Tier Layered dbt Architecture**:
```
 [ Staging Layer ]       ──►   [ Intermediate Layer ]   ──►   [ Marts Layer ]
 (Clean, Typecast, Dedupe)     (Enrich, Daypart, Grain)       (Business Intelligence)
```

1. **Staging (`models/staging/`):** 1-to-1 clean representations of source tables. Removes invalid coordinates, casts datatypes, standardizes timestamps to ISO-8601 UTC.
2. **Intermediate (`models/intermediate/`):** Business logic layer. Enforces dwell time thresholds ($5 \le \Delta t \le 180\text{ min}$), extracts temporal dimensions (daypart, weekday/weekend), and joins store/zone spatial contexts.
3. **Marts (`models/marts/`):** Dimension and fact models designed for high-performance dashboard consumption (Kepler.gl, Plotly) and strategic retail reporting.

---

## 2. Model Dependency Lineage (DAG)

```
   [raw_gps_mobility]        [raw_store_locations]       [detected_store_visits]     [commercial_zones]   [store_zone_mapping]
           │                           │                            │                          │                  │
           ▼                           ▼                            ▼                          ▼                  ▼
   stg_gps_mobility           stg_store_locations           stg_store_visits         stg_commercial_zones   stg_store_zone_mapping
                                       │                            │                                             │
                                       └─────────────┬──────────────┘                                             │
                                                     ▼                                                            │
                                          int_valid_store_visits                                                  │
                                                     │                                                            │
                                                     ▼                                                            │
                                         int_visit_time_dimensions                                                │
                                                     │                                                            │
                                                     ├────────────────────────────────────────────────────────────┤
                                                     │                                                            ▼
                                                     │                                                  int_visit_zone_mapping
                                                     ▼                                                            │
                                          int_store_footfall_base                                                 │
                                                     │                                                            │
                                                     ├──────────────────────────┬─────────────────────────────────┤
                                                     ▼                          ▼                                 ▼
                                            mart_hourly_footfall        mart_daily_footfall              mart_store_footfall
                                                     │                          │                                 │
                                                     └──────────────────────────┴───────────────┬─────────────────┘
                                                                                                ▼
                                                                                      mart_store_performance
                                                                                      mart_zone_footfall
```

---

## 3. Model Inventory & Specification

### 3.1 Staging Models (`models/staging/`)
- `stg_gps_mobility.sql`: Filters out-of-bounds latitude/longitude, standardizes timestamps, derives observation date and hour.
- `stg_store_locations.sql`: Cleans store master catalog, normalizes operational status (`active`, `inactive`).
- `stg_store_visits.sql`: Standardizes detected store visits, derives arrival date and hour, filters non-positive dwell times.
- `stg_commercial_zones.sql`: Standardizes commercial zone polygon geometries, types, and geodesic areas.
- `stg_store_zone_mapping.sql`: Spatial point-in-polygon assignment between stores and commercial zones.

### 3.2 Intermediate Models (`models/intermediate/`)
- `int_valid_store_visits.sql`: Restricts analysis to confirmed visits at active retail stores with verified dwell duration ($5.0 \le \text{dwell} \le 180.0\text{ min}$).
- `int_visit_time_dimensions.sql`: Enriches visits with calendar attributes: `day_of_week_name`, `is_weekend`, and `daypart_bucket` (`Morning: 6-11`, `Afternoon: 12-16`, `Evening: 17-21`, `Night: 22-5`).
- `int_visit_zone_mapping.sql`: Spatial join assigning zone context to visits while preserving strict 1-to-1 visit cardinality.
- `int_store_footfall_base.sql`: Baseline daily aggregation by store and date, computing daily visit totals and average dwell time.

### 3.3 Marts Models (`models/marts/`)
- `mart_store_footfall.sql`: Store-level dimensional mart aggregating total footfall, unique patron count, dwell duration, and portfolio rank.
- `mart_hourly_footfall.sql`: Hourly traffic distribution per store, calculating hourly traffic share percentage and peak operational hour flags.
- `mart_daily_footfall.sql`: Daily store performance assessing day-of-week trends and baseline ratio index.
- `mart_zone_footfall.sql`: Commercial zone vitality scorecard analyzing store density, total footfall, and visit density per $\text{km}^2$.
- `mart_store_performance.sql`: Holistic store scorecard tracking volume, repeat visitor rates, peak hour, weekday vs. weekend split, and category rank.

---

## 4. Local Execution & In-Warehouse Portability

To support development across local sandboxes and live cloud warehouses:
1. **ANSI Standard SQL:** All 14 models are authored in standard ANSI SQL with standard window functions (`DENSE_RANK()`, `ROW_NUMBER()`, `PARTITION BY`, `COALESCE`, `CASE`).
2. **dbt Local Runner (`dbt_geopulse/local_runner.py`):** An in-memory SQL execution harness that loads processed CSVs, executes all 14 models, persists mart CSVs to `data/processed/marts/`, and validates test assertions.
3. **Snowflake Profile (`dbt_geopulse/profiles.yml.example`):** Fully configured for direct connection to Snowflake `GEOPULSE_DB` when credentials are provided.
