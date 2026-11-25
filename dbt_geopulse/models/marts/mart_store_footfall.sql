-- Mart Model: mart_store_footfall
-- Store-level footfall analytics aggregating total visits, unique visitors, dwell time, and portfolio rankings

WITH visits AS (
    SELECT * FROM {{ ref('int_visit_zone_mapping') }}
),

daily_base AS (
    SELECT * FROM {{ ref('int_store_footfall_base') }}
),

store_aggregates AS (
    SELECT
        v.store_id,
        v.store_name,
        v.store_category,
        v.zone_id,
        v.zone_name,
        COUNT(DISTINCT v.visit_id) AS total_visits,
        COUNT(DISTINCT v.user_id) AS unique_visitors,
        ROUND(AVG(v.dwell_time_minutes), 2) AS avg_dwell_time_minutes,
        MIN(v.visit_date) AS first_visit_date,
        MAX(v.visit_date) AS last_visit_date,
        COUNT(DISTINCT v.visit_date) AS active_days_count
    FROM visits v
    GROUP BY
        v.store_id,
        v.store_name,
        v.store_category,
        v.zone_id,
        v.zone_name
),

ranked AS (
    SELECT
        store_id,
        store_name,
        store_category,
        zone_id,
        zone_name,
        total_visits,
        unique_visitors,
        avg_dwell_time_minutes,
        ROUND(CAST(total_visits AS FLOAT) / CAST(active_days_count AS FLOAT), 2) AS daily_avg_footfall,
        first_visit_date,
        last_visit_date,
        DENSE_RANK() OVER (ORDER BY total_visits DESC) AS store_footfall_rank,
        ROUND((CAST(total_visits - unique_visitors AS FLOAT) / CAST(total_visits AS FLOAT)) * 100.0, 2) AS repeat_visit_rate_pct
    FROM store_aggregates
)

SELECT * FROM ranked
ORDER BY store_footfall_rank ASC
