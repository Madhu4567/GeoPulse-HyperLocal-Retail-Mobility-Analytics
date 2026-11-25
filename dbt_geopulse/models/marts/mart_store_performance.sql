-- Mart Model: mart_store_performance
-- Holistic store performance profiling combining footfall volume, dwell engagement, peak hours, and weekend lift

WITH visits AS (
    SELECT * FROM {{ ref('int_visit_zone_mapping') }}
),

store_overview AS (
    SELECT
        store_id,
        store_name,
        store_category,
        zone_id,
        zone_name,
        COUNT(DISTINCT visit_id) AS total_footfall,
        COUNT(DISTINCT user_id) AS unique_visitors,
        ROUND(AVG(dwell_time_minutes), 2) AS avg_dwell_time_minutes,
        ROUND((CAST(COUNT(DISTINCT visit_id) - COUNT(DISTINCT user_id) AS FLOAT) / CAST(COUNT(DISTINCT visit_id) AS FLOAT)) * 100.0, 2) AS repeat_visitor_rate_pct
    FROM visits
    GROUP BY
        store_id,
        store_name,
        store_category,
        zone_id,
        zone_name
),

daypart_breakdown AS (
    SELECT
        store_id,
        SUM(CASE WHEN is_weekend = FALSE THEN 1 ELSE 0 END) AS weekday_visits,
        SUM(CASE WHEN is_weekend = TRUE THEN 1 ELSE 0 END) AS weekend_visits
    FROM visits
    GROUP BY store_id
),

peak_hour_calculation AS (
    SELECT
        store_id,
        arrival_hour AS peak_hour,
        ROW_NUMBER() OVER (PARTITION BY store_id ORDER BY COUNT(*) DESC, arrival_hour ASC) AS rank_hr
    FROM visits
    GROUP BY store_id, arrival_hour
),

store_peaks AS (
    SELECT store_id, peak_hour FROM peak_hour_calculation WHERE rank_hr = 1
),

final_performance AS (
    SELECT
        so.store_id,
        so.store_name,
        so.store_category,
        so.zone_name,
        so.total_footfall,
        so.unique_visitors,
        so.repeat_visitor_rate_pct,
        sp.peak_hour,
        so.avg_dwell_time_minutes,
        db.weekday_visits,
        db.weekend_visits,
        -- Weekend lift ratio normalized for 5 weekdays vs 2 weekend days
        ROUND(
            (CAST(db.weekend_visits AS FLOAT) / 2.0) /
            NULLIF((CAST(db.weekday_visits AS FLOAT) / 5.0), 0.0),
            2
        ) AS weekend_lift_ratio,
        DENSE_RANK() OVER (ORDER BY so.total_footfall DESC) AS portfolio_rank,
        RANK() OVER (PARTITION BY so.store_category ORDER BY so.total_footfall DESC) AS category_rank
    FROM store_overview so
    INNER JOIN daypart_breakdown db ON so.store_id = db.store_id
    INNER JOIN store_peaks sp ON so.store_id = sp.store_id
)

SELECT * FROM final_performance
ORDER BY portfolio_rank ASC
