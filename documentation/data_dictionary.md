# GeoPulse — Data Dictionary

> **Document**: Data Dictionary
> **Project**: GeoPulse — Hyper-Local Retail Mobility Analytics
> **Phase**: Day 3 — Database & Schema Design
> **Last Updated**: 2026-11-15
> **Status**: DRAFT

---

## Table of Contents

1. [Global Standards & Conventions](#1-global-standards--conventions)
2. [RAW Schema](#2-raw-schema)
3. [STAGING Schema](#3-staging-schema)
4. [INTERMEDIATE Schema](#4-intermediate-schema)
5. [MARTS Schema](#5-marts-schema)
6. [Enumeration Reference](#6-enumeration-reference)

---

## 1. Global Standards & Conventions

### Coordinate Reference System

| Property | Value |
|----------|-------|
| **CRS** | WGS 84 |
| **EPSG Code** | 4326 |
| **Latitude Range** | -90.0 to +90.0 (decimal degrees) |
| **Longitude Range** | -180.0 to +180.0 (decimal degrees) |
| **Geometry Format** | Well-Known Text (WKT) stored as `VARCHAR` |

### Timestamp Standard

| Property | Value |
|----------|-------|
| **Time Zone** | UTC (Coordinated Universal Time) |
| **Snowflake Type** | `TIMESTAMP_NTZ` (no time zone) |
| **Format** | ISO 8601: `YYYY-MM-DDTHH:MI:SS.FFF` |

### ID Conventions

| Entity | Prefix | Format Example | Max Length |
|--------|--------|----------------|-----------|
| User | `USR_` | `USR_00001` | 50 chars |
| Store | `STR_` | `STR_00042` | 50 chars |
| Zone | `ZN_` | `ZN_00007` | 50 chars |
| Visit | `VST_` | `VST_USR00001_STR00042_20260115` | 100 chars |

### Unit Conventions

| Measurement | Unit | Precision |
|-------------|------|-----------|
| Distance | Kilometers (km) | 3 decimal places |
| Dwell Time | Minutes | 1 decimal place |
| Area | Square kilometers (km²) | 4 decimal places |
| GPS Accuracy | Meters (m) | 1 decimal place |
| Percentages | 0–100 scale | 2 decimal places |

---

## 2. RAW Schema

### 2.1 `RAW.raw_gps_mobility`

> Synthetic GPS pings representing user mobility across the study area.

| Column | Data Type | Nullable | Description | Example Value | Validation Rules |
|--------|-----------|----------|-------------|---------------|-----------------|
| `user_id` | `VARCHAR(50)` | N | Unique user identifier | `USR_00001` | NOT NULL; must match `^USR_\d+$`; max 50 chars |
| `timestamp` | `TIMESTAMP_NTZ` | N | UTC time of GPS ping | `2026-01-15T09:32:15.000` | NOT NULL; must be valid timestamp; no future dates |
| `latitude` | `FLOAT` | N | Latitude in decimal degrees | `51.5074` | NOT NULL; range [-90, 90] |
| `longitude` | `FLOAT` | N | Longitude in decimal degrees | `-0.1278` | NOT NULL; range [-180, 180] |
| `accuracy` | `FLOAT` | Y | GPS accuracy radius in meters | `12.5` | If present, must be > 0 |
| `_loaded_at` | `TIMESTAMP_NTZ` | Y | Timestamp when row was loaded | `2026-01-16T00:00:00.000` | Auto-populated; DEFAULT CURRENT_TIMESTAMP() |

**Primary Key**: `(user_id, timestamp)`

---

### 2.2 `RAW.raw_retail_stores`

> Master data for retail store locations and attributes.

| Column | Data Type | Nullable | Description | Example Value | Validation Rules |
|--------|-----------|----------|-------------|---------------|-----------------|
| `store_id` | `VARCHAR(50)` | N | Unique store identifier | `STR_00042` | NOT NULL; must match `^STR_\d+$`; max 50 chars |
| `store_name` | `VARCHAR(255)` | N | Human-readable store name | `Fresh Mart Central` | NOT NULL; non-empty after trim |
| `latitude` | `FLOAT` | N | Store latitude (WGS 84) | `51.5155` | NOT NULL; range [-90, 90] |
| `longitude` | `FLOAT` | N | Store longitude (WGS 84) | `-0.0922` | NOT NULL; range [-180, 180] |
| `store_category` | `VARCHAR(50)` | N | Business category | `grocery` | NOT NULL; must be valid enum value (see §6) |
| `opening_date` | `DATE` | Y | Date the store opened | `2024-03-15` | If present, must be ≤ current date |
| `store_status` | `VARCHAR(20)` | N | Operational status | `active` | NOT NULL; must be valid enum value (see §6); DEFAULT 'active' |
| `_loaded_at` | `TIMESTAMP_NTZ` | Y | Row load timestamp | `2026-01-16T00:00:00.000` | Auto-populated; DEFAULT CURRENT_TIMESTAMP() |

**Primary Key**: `store_id`

---

### 2.3 `RAW.raw_commercial_zones`

> Commercial zone boundary definitions with WKT geometry.

| Column | Data Type | Nullable | Description | Example Value | Validation Rules |
|--------|-----------|----------|-------------|---------------|-----------------|
| `zone_id` | `VARCHAR(50)` | N | Unique zone identifier | `ZN_00007` | NOT NULL; must match `^ZN_\d+$`; max 50 chars |
| `zone_name` | `VARCHAR(255)` | N | Human-readable zone name | `Canary Wharf Mall` | NOT NULL; non-empty after trim |
| `zone_type` | `VARCHAR(50)` | N | Zone classification | `mall` | NOT NULL; must be valid enum value (see §6) |
| `geometry` | `VARCHAR(16777216)` | N | Zone boundary in WKT | `POLYGON((-0.1 51.5, ...))` | NOT NULL; must be valid WKT POLYGON or MULTIPOLYGON |
| `area_sq_km` | `FLOAT` | N | Zone area | `0.4500` | NOT NULL; must be > 0 |
| `_loaded_at` | `TIMESTAMP_NTZ` | Y | Row load timestamp | `2026-01-16T00:00:00.000` | Auto-populated; DEFAULT CURRENT_TIMESTAMP() |

**Primary Key**: `zone_id`

---

## 3. STAGING Schema

### 3.1 `STAGING.stg_gps_mobility`

> Cleaned, validated, and enriched GPS mobility data.

| Column | Data Type | Nullable | Description | Example Value | Validation Rules |
|--------|-----------|----------|-------------|---------------|-----------------|
| `user_id` | `VARCHAR(50)` | N | Trimmed user ID | `USR_00001` | From RAW; trimmed; non-null validated |
| `timestamp` | `TIMESTAMP_NTZ` | N | UTC timestamp of ping | `2026-01-15T09:32:15.000` | From RAW; non-null validated |
| `latitude` | `FLOAT` | N | Validated latitude | `51.5074` | Range-checked [-90, 90] |
| `longitude` | `FLOAT` | N | Validated longitude | `-0.1278` | Range-checked [-180, 180] |
| `accuracy` | `FLOAT` | Y | GPS accuracy in meters | `12.5` | Positive if present |
| `date_only` | `DATE` | N | Date extracted from timestamp | `2026-01-15` | Derived: `CAST(timestamp AS DATE)` |
| `hour_of_day` | `INTEGER` | N | Hour extracted (0–23) | `9` | Derived: `EXTRACT(HOUR FROM timestamp)` |
| `day_of_week` | `INTEGER` | N | Day of week (0=Mon…6=Sun) | `3` | Derived: `DAYOFWEEK(timestamp)` |
| `_loaded_at` | `TIMESTAMP_NTZ` | Y | Passthrough metadata | `2026-01-16T00:00:00.000` | From RAW |

---

### 3.2 `STAGING.stg_retail_stores`

> Validated retail store dimension.

| Column | Data Type | Nullable | Description | Example Value | Validation Rules |
|--------|-----------|----------|-------------|---------------|-----------------|
| `store_id` | `VARCHAR(50)` | N | Trimmed store ID | `STR_00042` | Non-null; prefix validated |
| `store_name` | `VARCHAR(255)` | N | Trimmed store name | `Fresh Mart Central` | Non-empty after trim |
| `latitude` | `FLOAT` | N | Validated latitude | `51.5155` | Range [-90, 90] |
| `longitude` | `FLOAT` | N | Validated longitude | `-0.0922` | Range [-180, 180] |
| `store_category` | `VARCHAR(50)` | N | Lowercased category | `grocery` | Must be valid enum |
| `opening_date` | `DATE` | Y | Store opening date | `2024-03-15` | ≤ current date |
| `store_status` | `VARCHAR(20)` | N | Lowercased status | `active` | Must be valid enum |
| `_loaded_at` | `TIMESTAMP_NTZ` | Y | Passthrough metadata | `2026-01-16T00:00:00.000` | From RAW |

---

### 3.3 `STAGING.stg_commercial_zones`

> Validated commercial zone data with geometry.

| Column | Data Type | Nullable | Description | Example Value | Validation Rules |
|--------|-----------|----------|-------------|---------------|-----------------|
| `zone_id` | `VARCHAR(50)` | N | Trimmed zone ID | `ZN_00007` | Non-null; prefix validated |
| `zone_name` | `VARCHAR(255)` | N | Trimmed zone name | `Canary Wharf Mall` | Non-empty after trim |
| `zone_type` | `VARCHAR(50)` | N | Lowercased zone type | `mall` | Must be valid enum |
| `geometry` | `VARCHAR(16777216)` | N | Validated WKT geometry | `POLYGON((-0.1 51.5, ...))` | Valid WKT; non-empty |
| `area_sq_km` | `FLOAT` | N | Zone area in km² | `0.4500` | > 0 |
| `_loaded_at` | `TIMESTAMP_NTZ` | Y | Passthrough metadata | `2026-01-16T00:00:00.000` | From RAW |

---

### 3.4 `STAGING.stg_store_visits`

> Derived store visit events from GPS proximity analysis.

| Column | Data Type | Nullable | Description | Example Value | Validation Rules |
|--------|-----------|----------|-------------|---------------|-----------------|
| `visit_id` | `VARCHAR(100)` | N | Unique visit identifier | `VST_USR00001_STR00042_20260115` | Non-null; `VST_` prefix |
| `user_id` | `VARCHAR(50)` | N | Visiting user | `USR_00001` | Must exist in stg_gps_mobility |
| `store_id` | `VARCHAR(50)` | N | Visited store | `STR_00042` | Must exist in stg_retail_stores |
| `arrival_time` | `TIMESTAMP_NTZ` | N | Visit start (UTC) | `2026-01-15T09:30:00.000` | < departure_time |
| `departure_time` | `TIMESTAMP_NTZ` | N | Visit end (UTC) | `2026-01-15T10:15:00.000` | > arrival_time |
| `dwell_time_minutes` | `FLOAT` | N | Duration of visit | `45.0` | > 0; = DATEDIFF(min, arrival, departure) |
| `distance_km` | `FLOAT` | N | User-to-store distance | `0.250` | ≥ 0; reasonable upper bound (< 50 km) |
| `visit_date` | `DATE` | N | Date of the visit | `2026-01-15` | Derived: `CAST(arrival_time AS DATE)` |

---

## 4. INTERMEDIATE Schema

### 4.1 `INTERMEDIATE.int_store_daily_footfall`

> Daily footfall aggregation per store.

| Column | Data Type | Nullable | Description | Example Value | Validation Rules |
|--------|-----------|----------|-------------|---------------|-----------------|
| `store_id` | `VARCHAR(50)` | N | Store identifier | `STR_00042` | FK to stg_retail_stores |
| `visit_date` | `DATE` | N | Date of aggregation | `2026-01-15` | Valid date |
| `total_visits` | `INTEGER` | N | Total visit count | `127` | ≥ 0 |
| `unique_visitors` | `INTEGER` | N | Distinct visitor count | `89` | ≥ 0; ≤ total_visits |
| `avg_dwell_time` | `FLOAT` | N | Mean dwell time (min) | `23.5` | ≥ 0 |
| `total_dwell_time` | `FLOAT` | N | Sum of dwell times (min) | `2984.5` | ≥ 0 |

---

### 4.2 `INTERMEDIATE.int_store_hourly_footfall`

> Hourly footfall breakdown per store per day.

| Column | Data Type | Nullable | Description | Example Value | Validation Rules |
|--------|-----------|----------|-------------|---------------|-----------------|
| `store_id` | `VARCHAR(50)` | N | Store identifier | `STR_00042` | FK to stg_retail_stores |
| `visit_date` | `DATE` | N | Date of aggregation | `2026-01-15` | Valid date |
| `hour_of_day` | `INTEGER` | N | Hour (0–23) | `14` | Range [0, 23] |
| `visit_count` | `INTEGER` | N | Visits in this hour | `18` | ≥ 0 |
| `unique_visitors` | `INTEGER` | N | Distinct visitors this hour | `15` | ≥ 0; ≤ visit_count |

---

### 4.3 `INTERMEDIATE.int_store_catchment_points`

> Individual user-to-store proximity records for catchment mapping.

| Column | Data Type | Nullable | Description | Example Value | Validation Rules |
|--------|-----------|----------|-------------|---------------|-----------------|
| `store_id` | `VARCHAR(50)` | N | Store identifier | `STR_00042` | FK to stg_retail_stores |
| `user_id` | `VARCHAR(50)` | N | User identifier | `USR_00001` | FK to stg_gps_mobility |
| `user_latitude` | `FLOAT` | N | User centroid latitude | `51.5100` | Range [-90, 90] |
| `user_longitude` | `FLOAT` | N | User centroid longitude | `-0.1050` | Range [-180, 180] |
| `distance_km` | `FLOAT` | N | Haversine distance (km) | `1.250` | ≥ 0 |
| `visit_count` | `INTEGER` | N | Total visits by this user | `5` | ≥ 1 |

---

### 4.4 `INTERMEDIATE.int_zone_store_mapping`

> Maps each store to the commercial zone it resides in.

| Column | Data Type | Nullable | Description | Example Value | Validation Rules |
|--------|-----------|----------|-------------|---------------|-----------------|
| `zone_id` | `VARCHAR(50)` | N | Zone identifier | `ZN_00007` | FK to stg_commercial_zones |
| `store_id` | `VARCHAR(50)` | N | Store identifier | `STR_00042` | FK to stg_retail_stores |
| `store_name` | `VARCHAR(255)` | N | Store name | `Fresh Mart Central` | Non-empty |
| `is_within_zone` | `BOOLEAN` | N | Spatial containment flag | `TRUE` | TRUE or FALSE |

---

## 5. MARTS Schema

### 5.1 `MARTS.mart_store_footfall_summary`

> Lifetime footfall summary per store.

| Column | Data Type | Nullable | Description | Example Value | Validation Rules |
|--------|-----------|----------|-------------|---------------|-----------------|
| `store_id` | `VARCHAR(50)` | N | Store identifier | `STR_00042` | Unique per row |
| `store_name` | `VARCHAR(255)` | N | Store name | `Fresh Mart Central` | Non-empty |
| `store_category` | `VARCHAR(50)` | N | Store category | `grocery` | Valid enum |
| `total_visits` | `INTEGER` | N | Lifetime total visits | `3854` | ≥ 0 |
| `unique_visitors` | `INTEGER` | N | Lifetime unique visitors | `1203` | ≥ 0; ≤ total_visits |
| `avg_daily_visits` | `FLOAT` | N | Mean visits per day | `128.5` | ≥ 0 |
| `avg_dwell_minutes` | `FLOAT` | N | Mean dwell time (min) | `22.3` | ≥ 0 |
| `peak_hour` | `INTEGER` | N | Busiest hour (0–23) | `13` | Range [0, 23] |
| `busiest_day` | `INTEGER` | N | Busiest day of week | `5` | Range [0, 6] |

---

### 5.2 `MARTS.mart_hourly_traffic_patterns`

> Hourly traffic distribution for time-of-day & day-of-week analysis.

| Column | Data Type | Nullable | Description | Example Value | Validation Rules |
|--------|-----------|----------|-------------|---------------|-----------------|
| `store_id` | `VARCHAR(50)` | N | Store identifier | `STR_00042` | FK |
| `store_name` | `VARCHAR(255)` | N | Store name | `Fresh Mart Central` | Non-empty |
| `hour_of_day` | `INTEGER` | N | Hour (0–23) | `14` | Range [0, 23] |
| `day_of_week` | `INTEGER` | N | Day (0=Mon…6=Sun) | `2` | Range [0, 6] |
| `avg_visits` | `FLOAT` | N | Average visits | `15.7` | ≥ 0 |
| `pct_of_daily_traffic` | `FLOAT` | N | % of daily traffic | `8.45` | Range [0, 100]; sum per store/day ≈ 100 |

---

### 5.3 `MARTS.mart_store_catchment_areas`

> Store catchment area geographic summary.

| Column | Data Type | Nullable | Description | Example Value | Validation Rules |
|--------|-----------|----------|-------------|---------------|-----------------|
| `store_id` | `VARCHAR(50)` | N | Store identifier | `STR_00042` | Unique per row |
| `store_name` | `VARCHAR(255)` | N | Store name | `Fresh Mart Central` | Non-empty |
| `catchment_radius_km` | `FLOAT` | N | Effective radius (90th pctl) | `2.500` | > 0 |
| `total_users_in_catchment` | `INTEGER` | N | Users within catchment | `342` | ≥ 0 |
| `avg_distance_km` | `FLOAT` | N | Mean user distance | `1.150` | ≥ 0 |
| `max_distance_km` | `FLOAT` | N | Maximum user distance | `4.800` | ≥ avg_distance_km |
| `catchment_area_sq_km` | `FLOAT` | N | π × r² (approx.) | `19.6350` | > 0 |

---

### 5.4 `MARTS.mart_catchment_overlap`

> Pairwise store catchment overlap analysis.

| Column | Data Type | Nullable | Description | Example Value | Validation Rules |
|--------|-----------|----------|-------------|---------------|-----------------|
| `store_id_a` | `VARCHAR(50)` | N | First store (alphabetically) | `STR_00010` | store_id_a < store_id_b |
| `store_id_b` | `VARCHAR(50)` | N | Second store | `STR_00042` | store_id_b > store_id_a |
| `store_name_a` | `VARCHAR(255)` | N | Name of store A | `City Books` | Non-empty |
| `store_name_b` | `VARCHAR(255)` | N | Name of store B | `Fresh Mart Central` | Non-empty |
| `shared_users` | `INTEGER` | N | Users visiting both | `47` | ≥ 0 |
| `overlap_pct_a` | `FLOAT` | N | % of A's users shared | `12.50` | Range [0, 100] |
| `overlap_pct_b` | `FLOAT` | N | % of B's users shared | `8.75` | Range [0, 100] |
| `distance_between_stores_km` | `FLOAT` | N | Haversine between stores | `0.850` | > 0 |

---

### 5.5 `MARTS.mart_cannibalization_risk`

> Cannibalization risk scoring for store pairs.

| Column | Data Type | Nullable | Description | Example Value | Validation Rules |
|--------|-----------|----------|-------------|---------------|-----------------|
| `store_id_a` | `VARCHAR(50)` | N | First store | `STR_00010` | store_id_a < store_id_b |
| `store_id_b` | `VARCHAR(50)` | N | Second store | `STR_00042` | store_id_b > store_id_a |
| `store_name_a` | `VARCHAR(255)` | N | Name of store A | `City Books` | Non-empty |
| `store_name_b` | `VARCHAR(255)` | N | Name of store B | `Fresh Mart Central` | Non-empty |
| `shared_visitors` | `INTEGER` | N | Count of shared visitors | `47` | ≥ 0 |
| `cannibalization_score` | `FLOAT` | N | Composite risk score | `0.72` | Range [0.0, 1.0] |
| `risk_level` | `VARCHAR(10)` | N | Categorical risk label | `high` | Enum: low / medium / high |
| `distance_km` | `FLOAT` | N | Distance between stores | `0.850` | > 0 |
| `same_category` | `BOOLEAN` | N | Same store category? | `TRUE` | TRUE or FALSE |

---

### 5.6 `MARTS.mart_zone_performance`

> Zone-level performance metrics for commercial area benchmarking.

| Column | Data Type | Nullable | Description | Example Value | Validation Rules |
|--------|-----------|----------|-------------|---------------|-----------------|
| `zone_id` | `VARCHAR(50)` | N | Zone identifier | `ZN_00007` | Unique per row |
| `zone_name` | `VARCHAR(255)` | N | Zone name | `Canary Wharf Mall` | Non-empty |
| `zone_type` | `VARCHAR(50)` | N | Zone classification | `mall` | Valid enum |
| `num_stores` | `INTEGER` | N | Stores in zone | `12` | ≥ 0 |
| `total_zone_visits` | `INTEGER` | N | Sum of all store visits | `15420` | ≥ 0 |
| `avg_store_visits` | `FLOAT` | N | Mean visits per store | `1285.0` | ≥ 0 |
| `total_unique_visitors` | `INTEGER` | N | Distinct visitors in zone | `4230` | ≥ 0 |
| `zone_density_score` | `FLOAT` | N | Visits per km² | `34266.7` | ≥ 0; = total_zone_visits / area_sq_km |

---

## 6. Enumeration Reference

### `store_category`

| Value | Description |
|-------|-------------|
| `grocery` | Supermarkets and food stores |
| `fashion` | Clothing and apparel retailers |
| `electronics` | Consumer electronics stores |
| `restaurant` | Dining establishments |
| `pharmacy` | Pharmacies and drugstores |
| `convenience` | Convenience / corner stores |
| `department_store` | Large multi-category department stores |

### `zone_type`

| Value | Description |
|-------|-------------|
| `mall` | Enclosed shopping mall / centre |
| `high_street` | Traditional high-street retail corridor |
| `retail_park` | Out-of-town retail park |
| `market` | Open-air or covered market area |
| `commercial_district` | Mixed-use commercial / business district |

### `store_status`

| Value | Description |
|-------|-------------|
| `active` | Currently operating |
| `inactive` | Temporarily not operating |
| `closed` | Permanently closed |

### `risk_level`

| Value | Score Range | Description |
|-------|------------|-------------|
| `low` | 0.00 – 0.33 | Minimal cannibalization concern |
| `medium` | 0.34 – 0.66 | Moderate overlap; monitor |
| `high` | 0.67 – 1.00 | Significant cannibalization risk; action recommended |

---

*End of Data Dictionary*
