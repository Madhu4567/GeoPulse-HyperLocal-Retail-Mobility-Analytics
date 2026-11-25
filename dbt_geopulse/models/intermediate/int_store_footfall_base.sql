-- Intermediate Model: int_store_footfall_base
-- Daily store-level aggregation calculating visits, unique visitors, and dwell time metrics

WITH visits AS (
    SELECT * FROM {{ ref('int_visit_time_dimensions') }}
),

daily_base AS (
    SELECT
        store_id,
        store_name,
        store_category,
        visit_date,
        day_of_week_name,
        is_weekend,
        COUNT(DISTINCT visit_id) AS daily_visits,
        COUNT(DISTINCT user_id) AS daily_unique_visitors,
        ROUND(AVG(dwell_time_minutes), 2) AS daily_avg_dwell_minutes,
        ROUND(SUM(dwell_time_minutes), 2) AS daily_total_dwell_minutes
    FROM visits
    GROUP BY
        store_id,
        store_name,
        store_category,
        visit_date,
        day_of_week_name,
        is_weekend
)

SELECT * FROM daily_base
