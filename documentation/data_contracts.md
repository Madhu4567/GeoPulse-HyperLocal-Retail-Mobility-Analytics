# GeoPulse — Data Contracts

> **Document**: Data Contracts
> **Project**: GeoPulse — Hyper-Local Retail Mobility Analytics
> **Phase**: Day 3 — Database & Schema Design
> **Last Updated**: 2026-11-15
> **Status**: DRAFT

---

## Table of Contents

1. [Contract 1: GPS Mobility Data](#contract-1-gps-mobility-data)
2. [Contract 2: Retail Store Data](#contract-2-retail-store-data)
3. [Contract 3: Commercial Zone Data](#contract-3-commercial-zone-data)
4. [Contract 4: Processed Store Visits](#contract-4-processed-store-visits)
5. [Contract 5: dbt Mart Outputs](#contract-5-dbt-mart-outputs)

---

## Contract Overview

```
Module 1 (Data Eng)                    Module 2 (Analytics)
┌──────────────────┐                   ┌──────────────────────┐
│ GPS Generation   │──Contract 1──►    │                      │
│ Store Generation │──Contract 2──►    │  Snowflake RAW       │
│                  │                   │      │                │
│                  │   Contract 3  ◄── │  Zone Data Prep      │
│                  │                   │                      │
│ Visit Processing │──Contract 4──►    │  dbt STAGING →       │
│                  │                   │  INTERMEDIATE →      │
│                  │                   │  MARTS               │
│                  │   Contract 5  ◄── │      │                │
│                  │                   │  Dashboard/Kepler.gl │
└──────────────────┘                   └──────────────────────┘
```

---

## Contract 1: GPS Mobility Data

### Metadata

| Field | Value |
|-------|-------|
| **Contract ID** | `DC-001` |
| **Name** | GPS Mobility Data |
| **Provider** | Module 1 — Data Engineering (Synthetic GPS Data Generation) |
| **Consumer** | Snowflake `RAW.raw_gps_mobility` |
| **Format** | CSV (UTF-8, header row, comma-delimited) |
| **Delivery** | File staged to Snowflake internal stage `@GEOPULSE_DB.RAW.gps_stage` |
| **Frequency** | One-time batch load (synthetic data); future: daily incremental |

### Schema

| Column | Data Type | Required | Description |
|--------|-----------|----------|-------------|
| `user_id` | `VARCHAR(50)` | ✅ | Unique user ID with `USR_` prefix |
| `timestamp` | `TIMESTAMP_NTZ` | ✅ | UTC timestamp of GPS ping (ISO 8601) |
| `latitude` | `FLOAT` | ✅ | WGS 84 latitude [-90, 90] |
| `longitude` | `FLOAT` | ✅ | WGS 84 longitude [-180, 180] |
| `accuracy` | `FLOAT` | ❌ | GPS accuracy in meters (> 0) |

### Quality Rules

| Rule ID | Rule | Severity | Action |
|---------|------|----------|--------|
| `Q1-01` | No NULL values in `user_id`, `timestamp`, `latitude`, `longitude` | 🔴 Critical | Reject row |
| `Q1-02` | Latitude in [-90, 90] | 🔴 Critical | Reject row |
| `Q1-03` | Longitude in [-180, 180] | 🔴 Critical | Reject row |
| `Q1-04` | `user_id` matches pattern `^USR_\d+$` | 🟡 Warning | Log & flag for review |
| `Q1-05` | Timestamp is not in the future | 🟡 Warning | Log & flag for review |
| `Q1-06` | No duplicate `(user_id, timestamp)` pairs | 🔴 Critical | Deduplicate; keep first |
| `Q1-07` | `accuracy` > 0 when present | 🟡 Warning | Set to NULL if invalid |
| `Q1-08` | Minimum 200,000 rows per batch | 🟡 Warning | Alert provider |

### Volume Expectations

| Metric | Expected Value |
|--------|---------------|
| Initial load | ~250,000 rows |
| Row size (avg) | ~120 bytes |
| File size | ~30 MB |
| Unique users | ~1,000 |
| Date range | 30 days |

### SLA

| Metric | Target |
|--------|--------|
| Delivery time | Within 24 hours of generation |
| Data freshness | Same-day for batch loads |
| Schema change notice | 48 hours minimum |
| Quality threshold | ≥ 99% rows pass all Critical rules |

### Failure Handling

| Scenario | Action |
|----------|--------|
| File not delivered on time | Provider notifies consumer via Slack/GitHub issue; pipeline waits |
| > 1% rows fail Critical rules | Load is rejected; provider re-generates and re-delivers |
| Schema change without notice | Consumer rejects load; escalate to team lead |
| Partial file / corrupt CSV | Consumer rejects; provider re-delivers complete file |

---

## Contract 2: Retail Store Data

### Metadata

| Field | Value |
|-------|-------|
| **Contract ID** | `DC-002` |
| **Name** | Retail Store Data |
| **Provider** | Module 1 — Data Engineering (Retail Store Data Generation) |
| **Consumer** | Snowflake `RAW.raw_retail_stores` |
| **Format** | CSV (UTF-8, header row, comma-delimited) |
| **Delivery** | File staged to `@GEOPULSE_DB.RAW.store_stage` |
| **Frequency** | One-time load; updated only when store list changes |

### Schema

| Column | Data Type | Required | Description |
|--------|-----------|----------|-------------|
| `store_id` | `VARCHAR(50)` | ✅ | Unique store ID with `STR_` prefix |
| `store_name` | `VARCHAR(255)` | ✅ | Human-readable store name |
| `latitude` | `FLOAT` | ✅ | Store latitude (WGS 84) |
| `longitude` | `FLOAT` | ✅ | Store longitude (WGS 84) |
| `store_category` | `VARCHAR(50)` | ✅ | Must be valid enum value |
| `opening_date` | `DATE` | ❌ | ISO 8601 date format |
| `store_status` | `VARCHAR(20)` | ✅ | Default: `active` |

### Quality Rules

| Rule ID | Rule | Severity | Action |
|---------|------|----------|--------|
| `Q2-01` | No NULL in required columns | 🔴 Critical | Reject row |
| `Q2-02` | `store_id` unique across file | 🔴 Critical | Reject duplicate; keep first |
| `Q2-03` | `store_id` matches `^STR_\d+$` | 🟡 Warning | Log & flag |
| `Q2-04` | Latitude in [-90, 90] | 🔴 Critical | Reject row |
| `Q2-05` | Longitude in [-180, 180] | 🔴 Critical | Reject row |
| `Q2-06` | `store_category` is valid enum | 🔴 Critical | Reject row |
| `Q2-07` | `store_status` is valid enum | 🔴 Critical | Default to `active` if missing |
| `Q2-08` | `opening_date` ≤ current date | 🟡 Warning | Log & flag |
| `Q2-09` | No two stores at identical coordinates | 🟡 Warning | Log & flag |

### Volume Expectations

| Metric | Expected Value |
|--------|---------------|
| Row count | 50–200 rows |
| File size | < 50 KB |
| Unique categories | 7 |

### SLA

| Metric | Target |
|--------|--------|
| Delivery time | Before GPS data delivery |
| Schema change notice | 48 hours minimum |
| Quality threshold | 100% rows pass Critical rules (small dataset) |

### Failure Handling

| Scenario | Action |
|----------|--------|
| Missing required columns | Reject entire file; provider re-generates |
| Invalid enum values | Reject affected rows; log for provider review |
| Empty file | Alert provider; pipeline blocks |

---

## Contract 3: Commercial Zone Data

### Metadata

| Field | Value |
|-------|-------|
| **Contract ID** | `DC-003` |
| **Name** | Commercial Zone Data |
| **Provider** | Module 2 — Analytics & Visualization (Commercial Zoning Data Prep) |
| **Consumer** | Snowflake `RAW.raw_commercial_zones` |
| **Format** | CSV (UTF-8, header row, comma-delimited); geometry as WKT string |
| **Delivery** | File staged to `@GEOPULSE_DB.RAW.zone_stage` |
| **Frequency** | One-time load; updated when zone boundaries are revised |

### Schema

| Column | Data Type | Required | Description |
|--------|-----------|----------|-------------|
| `zone_id` | `VARCHAR(50)` | ✅ | Unique zone ID with `ZN_` prefix |
| `zone_name` | `VARCHAR(255)` | ✅ | Human-readable zone name |
| `zone_type` | `VARCHAR(50)` | ✅ | Must be valid enum value |
| `geometry` | `VARCHAR` | ✅ | WKT POLYGON or MULTIPOLYGON |
| `area_sq_km` | `FLOAT` | ✅ | Zone area in km² (> 0) |

### Quality Rules

| Rule ID | Rule | Severity | Action |
|---------|------|----------|--------|
| `Q3-01` | No NULL in any column | 🔴 Critical | Reject row |
| `Q3-02` | `zone_id` unique across file | 🔴 Critical | Reject duplicate |
| `Q3-03` | `zone_id` matches `^ZN_\d+$` | 🟡 Warning | Log & flag |
| `Q3-04` | `zone_type` is valid enum | 🔴 Critical | Reject row |
| `Q3-05` | `geometry` is valid WKT (POLYGON/MULTIPOLYGON) | 🔴 Critical | Reject row |
| `Q3-06` | `area_sq_km` > 0 | 🔴 Critical | Reject row |
| `Q3-07` | Geometry coordinates within WGS 84 bounds | 🟡 Warning | Log & flag |
| `Q3-08` | No overlapping zones of the same type | 🟡 Warning | Log for review |

### Volume Expectations

| Metric | Expected Value |
|--------|---------------|
| Row count | 10–50 rows |
| File size | < 500 KB (WKT can be verbose) |
| Unique zone types | 5 |

### SLA

| Metric | Target |
|--------|--------|
| Delivery time | Before spatial processing begins |
| Schema change notice | 48 hours minimum |
| Quality threshold | 100% rows pass Critical rules |

### Failure Handling

| Scenario | Action |
|----------|--------|
| Invalid WKT geometry | Reject row; provider (Module 2) corrects and re-delivers |
| Missing columns | Reject entire file |
| Zero rows | Alert; pipeline blocks until data is provided |

---

## Contract 4: Processed Store Visits

> [!IMPORTANT]
> This is the **key handoff** between Module 1 (Data Engineering) and Module 2 (Analytics).
> Module 1 produces visit events from GPS proximity + nearest-store analysis.
> Module 2 consumes these events via dbt staging models for all downstream analytics.

### Metadata

| Field | Value |
|-------|-------|
| **Contract ID** | `DC-004` |
| **Name** | Processed Store Visits |
| **Provider** | Module 1 — Data Engineering (Nearest-Store Mapping + Visit Detection) |
| **Consumer** | Snowflake RAW → dbt staging (`STAGING.stg_store_visits`) → Module 2 analytics |
| **Format** | CSV (UTF-8, header row, comma-delimited) |
| **Delivery** | File staged to `@GEOPULSE_DB.RAW.visits_stage` |
| **Frequency** | One-time batch; future: after each GPS data refresh |

### Schema

| Column | Data Type | Required | Description |
|--------|-----------|----------|-------------|
| `visit_id` | `VARCHAR(100)` | ✅ | Unique visit identifier with `VST_` prefix |
| `user_id` | `VARCHAR(50)` | ✅ | User who made the visit; must exist in GPS data |
| `store_id` | `VARCHAR(50)` | ✅ | Store visited; must exist in store data |
| `arrival_time` | `TIMESTAMP_NTZ` | ✅ | Visit start time (UTC) |
| `departure_time` | `TIMESTAMP_NTZ` | ✅ | Visit end time (UTC) |
| `dwell_time_minutes` | `FLOAT` | ✅ | Visit duration in minutes |
| `distance_km` | `FLOAT` | ✅ | User-to-store Haversine distance (km) |
| `visit_date` | `DATE` | ✅ | Date derived from arrival_time |

### Quality Rules

| Rule ID | Rule | Severity | Action |
|---------|------|----------|--------|
| `Q4-01` | No NULL in any column | 🔴 Critical | Reject row |
| `Q4-02` | `visit_id` unique across file | 🔴 Critical | Deduplicate; keep first |
| `Q4-03` | `user_id` exists in `raw_gps_mobility` | 🔴 Critical | Reject row (referential integrity) |
| `Q4-04` | `store_id` exists in `raw_retail_stores` | 🔴 Critical | Reject row (referential integrity) |
| `Q4-05` | `arrival_time` < `departure_time` | 🔴 Critical | Reject row |
| `Q4-06` | `dwell_time_minutes` > 0 | 🔴 Critical | Reject row |
| `Q4-07` | `dwell_time_minutes` ≈ DATEDIFF(min, arrival, departure) ± 1 | 🟡 Warning | Recalculate in staging |
| `Q4-08` | `distance_km` ≥ 0 and < 50 | 🟡 Warning | Flag for review if > 10 km |
| `Q4-09` | `visit_date` = CAST(arrival_time AS DATE) | 🟡 Warning | Recalculate in staging |
| `Q4-10` | No user visiting two stores simultaneously | 🟡 Warning | Log; keep both (could be adjacent stores) |
| `Q4-11` | Minimum 10,000 visit rows | 🟡 Warning | Alert provider — may indicate proximity threshold issue |

### Volume Expectations

| Metric | Expected Value |
|--------|---------------|
| Row count | ~20,000–100,000 rows |
| Unique users | ~800–1,000 |
| Unique stores | 50–200 |
| Date range | 30 days |
| Avg dwell time | 5–60 minutes |

### SLA

| Metric | Target |
|--------|--------|
| Delivery time | Within 48 hours of GPS data load |
| Data freshness | Same batch as GPS data |
| Schema change notice | 72 hours minimum (critical interface) |
| Quality threshold | ≥ 98% rows pass all Critical rules |
| Redelivery turnaround | 24 hours after rejection |

### Failure Handling

| Scenario | Action |
|----------|--------|
| File not delivered on schedule | Module 2 pipeline blocked; escalate immediately |
| > 2% rows fail Critical rules | Entire load rejected; Module 1 re-processes with corrected thresholds |
| Referential integrity failures | Provider checks GPS/store data alignment; re-delivers |
| Schema mismatch | Consumer rejects; both modules meet to reconcile |
| Anomalously low row count | Joint review of proximity threshold and GPS data coverage |

### Interface Agreement

Both modules agree to the following coordination protocol:

1. **Module 1** notifies Module 2 (via GitHub issue or Slack) when visit data is ready
2. **Module 2** validates within 4 hours and confirms acceptance or raises issues
3. Any schema changes require a pull request reviewed by both modules
4. Proximity threshold (e.g., 100m for "near store") is agreed upon jointly and documented

---

## Contract 5: dbt Mart Outputs

### Metadata

| Field | Value |
|-------|-------|
| **Contract ID** | `DC-005` |
| **Name** | dbt Mart Outputs |
| **Provider** | Module 2 — Analytics & Visualization (dbt transformation models) |
| **Consumer** | Kepler.gl Dashboard, Plotly Visualizations, Business Reports |
| **Format** | Snowflake tables in `MARTS` schema |
| **Delivery** | Available after `dbt run` completes successfully |
| **Frequency** | On-demand; triggered by Airflow DAG or manual `dbt run` |

### Output Tables

| Table | Grain | Key Columns | Consumer Use Case |
|-------|-------|-------------|-------------------|
| `mart_store_footfall_summary` | 1 row per store | `store_id` | Executive KPI dashboard |
| `mart_hourly_traffic_patterns` | 1 row per store × hour × day | `store_id`, `hour_of_day`, `day_of_week` | Time-of-day heatmaps |
| `mart_store_catchment_areas` | 1 row per store | `store_id` | Catchment radius maps |
| `mart_catchment_overlap` | 1 row per store pair | `store_id_a`, `store_id_b` | Overlap chord diagrams |
| `mart_cannibalization_risk` | 1 row per store pair | `store_id_a`, `store_id_b` | Risk assessment reports |
| `mart_zone_performance` | 1 row per zone | `zone_id` | Zone benchmarking dashboard |

### Quality Rules

| Rule ID | Rule | Severity | Action |
|---------|------|----------|--------|
| `Q5-01` | All mart tables populated (row count > 0) | 🔴 Critical | dbt run fails; investigate upstream |
| `Q5-02` | No NULL in primary key columns | 🔴 Critical | dbt test failure; fix model logic |
| `Q5-03` | `pct_of_daily_traffic` sums to ~100 per store/day | 🟡 Warning | Review hourly aggregation logic |
| `Q5-04` | `cannibalization_score` in [0, 1] | 🔴 Critical | Fix scoring formula |
| `Q5-05` | `risk_level` is valid enum (low/medium/high) | 🔴 Critical | Fix CASE statement |
| `Q5-06` | `catchment_area_sq_km` ≈ π × catchment_radius² | 🟡 Warning | Review calculation |
| `Q5-07` | `unique_visitors` ≤ `total_visits` in all tables | 🔴 Critical | Fix aggregation logic |
| `Q5-08` | `zone_density_score` = `total_zone_visits / area_sq_km` | 🟡 Warning | Review formula |

### dbt Tests (Enforced)

```yaml
# schema.yml excerpt
models:
  - name: mart_store_footfall_summary
    columns:
      - name: store_id
        tests: [unique, not_null]
      - name: total_visits
        tests: [not_null]

  - name: mart_cannibalization_risk
    columns:
      - name: risk_level
        tests:
          - accepted_values:
              values: ['low', 'medium', 'high']
      - name: cannibalization_score
        tests:
          - dbt_utils.expression_is_true:
              expression: ">= 0 AND <= 1"

  - name: mart_zone_performance
    columns:
      - name: zone_id
        tests: [unique, not_null]
```

### SLA

| Metric | Target |
|--------|--------|
| `dbt run` completion | < 10 minutes for full refresh |
| `dbt test` pass rate | 100% Critical tests must pass |
| Data available after pipeline | Within 30 minutes of triggering |
| Schema change notice | 48 hours; dashboard consumer notified |

### Failure Handling

| Scenario | Action |
|----------|--------|
| `dbt run` fails | Airflow task retries once; if still fails, alert Module 2 |
| `dbt test` fails | Pipeline halts; mart tables remain at previous version |
| Upstream data missing | Pipeline blocked; trace to responsible contract (DC-001 through DC-004) |
| Dashboard shows stale data | Check Airflow DAG status; re-trigger if needed |
| Schema evolution needed | PR with migration plan; both modules + dashboard owner review |

---

## Contract Dependency Graph

```
DC-001 (GPS Mobility)      ──►  RAW.raw_gps_mobility
DC-002 (Retail Stores)     ──►  RAW.raw_retail_stores
DC-003 (Commercial Zones)  ──►  RAW.raw_commercial_zones
DC-004 (Store Visits)      ──►  RAW.raw_store_visits (handoff table)
                                        │
                                   dbt pipeline
                                        │
                                        ▼
DC-005 (Mart Outputs)      ◄──  MARTS.mart_*
                                        │
                                        ▼
                                   Dashboard / Reports
```

---

*End of Data Contracts*
