-- Mart Model: mart_hourly_footfall
-- Hourly footfall distribution per store identifying diurnal activity patterns and peak operational hours

WITH visits AS (
    SELECT * FROM {{ ref('int_visit_time_dimensions') }}
),

hourly_base AS (
    SELECT
        store_id,
        store_name,
        store_category,
        visit_date,
        arrival_hour AS hour_of_day,
        COUNT(DISTINCT visit_id) AS hourly_visits,
        COUNT(DISTINCT user_id) AS hourly_unique_visitors,
        ROUND(AVG(dwell_time_minutes), 2) AS avg_dwell_time_minutes
    FROM visits
    GROUP BY
        store_id,
        store_name,
        store_category,
        visit_date,
        arrival_hour
),

daily_totals AS (
    SELECT
        store_id,
        visit_date,
        SUM(hourly_visits) AS store_daily_total
    FROM hourly_base
    GROUP BY store_id, visit_date
),

ranked_hours AS (
    SELECT
        h.store_id,
        h.store_name,
        h.store_category,
        h.visit_date,
        h.hour_of_day,
        h.hourly_visits,
        h.hourly_unique_visitors,
        h.avg_dwell_time_minutes,
        ROUND((CAST(h.hourly_visits AS FLOAT) / CAST(d.store_daily_total AS FLOAT)) * 100.0, 2) AS hourly_traffic_share_pct,
        ROW_NUMBER() OVER (
            PARTITION BY h.store_id, h.visit_date
            ORDER BY h.hourly_visits DESC, h.hour_of_day ASC
        ) AS hour_traffic_rank
    FROM hourly_base h
    INNER JOIN daily_totals d
        ON h.store_id = d.store_id AND h.visit_date = d.visit_date
)

SELECT
    store_id,
    store_name,
    store_category,
    visit_date,
    hour_of_day,
    hourly_visits,
    hourly_unique_visitors,
    avg_dwell_time_minutes,
    hourly_traffic_share_pct,
    CASE WHEN hour_traffic_rank = 1 THEN TRUE ELSE FALSE END AS is_peak_hour
FROM ranked_hours
ORDER BY store_id, visit_date, hour_of_day
