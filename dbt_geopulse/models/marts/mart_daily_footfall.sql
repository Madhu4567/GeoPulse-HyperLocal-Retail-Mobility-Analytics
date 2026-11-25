-- Mart Model: mart_daily_footfall
-- Store daily footfall metrics evaluating day-of-week trends and weekday vs. weekend performance

WITH daily_base AS (
    SELECT * FROM {{ ref('int_store_footfall_base') }}
),

store_benchmarks AS (
    SELECT
        store_id,
        ROUND(AVG(daily_visits), 2) AS store_baseline_avg_daily_visits
    FROM daily_base
    GROUP BY store_id
),

evaluated AS (
    SELECT
        d.store_id,
        d.store_name,
        d.store_category,
        d.visit_date,
        d.day_of_week_name,
        d.is_weekend,
        d.daily_visits,
        d.daily_unique_visitors,
        d.daily_avg_dwell_minutes,
        d.daily_total_dwell_minutes,
        b.store_baseline_avg_daily_visits,
        ROUND(CAST(d.daily_visits AS FLOAT) / CAST(b.store_baseline_avg_daily_visits AS FLOAT), 2) AS daily_vs_average_ratio,
        CASE
            WHEN d.daily_visits >= b.store_baseline_avg_daily_visits * 1.15 THEN 'High Traffic'
            WHEN d.daily_visits <= b.store_baseline_avg_daily_visits * 0.85 THEN 'Low Traffic'
            ELSE 'Normal Traffic'
        END AS daily_performance_tier
    FROM daily_base d
    INNER JOIN store_benchmarks b
        ON d.store_id = b.store_id
)

SELECT * FROM evaluated
ORDER BY store_id, visit_date
