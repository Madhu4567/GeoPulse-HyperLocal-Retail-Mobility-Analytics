-- Mart Model: mart_zone_footfall
-- Commercial zone-level footfall analytics assessing store density, traffic capture, and retail vitality

WITH visits AS (
    SELECT * FROM {{ ref('int_visit_zone_mapping') }}
),

zones AS (
    SELECT * FROM {{ ref('stg_commercial_zones') }}
),

stores AS (
    SELECT * FROM {{ ref('stg_store_zone_mapping') }}
),

zone_store_counts AS (
    SELECT
        zone_id,
        COUNT(DISTINCT store_id) AS store_count
    FROM stores
    WHERE is_within_zone = TRUE
    GROUP BY zone_id
),

zone_metrics AS (
    SELECT
        v.zone_id,
        COUNT(DISTINCT v.visit_id) AS total_zone_visits,
        COUNT(DISTINCT v.user_id) AS unique_visitors,
        ROUND(AVG(v.dwell_time_minutes), 2) AS avg_dwell_time_minutes,
        COUNT(DISTINCT v.visit_date) AS active_days
    FROM visits v
    WHERE v.is_within_commercial_zone = TRUE
    GROUP BY v.zone_id
),

compiled AS (
    SELECT
        z.zone_id,
        z.zone_name,
        z.zone_type,
        z.area_sq_km,
        COALESCE(sc.store_count, 0) AS store_count,
        COALESCE(zm.total_zone_visits, 0) AS total_zone_visits,
        COALESCE(zm.unique_visitors, 0) AS unique_visitors,
        COALESCE(zm.avg_dwell_time_minutes, 0.0) AS avg_dwell_time_minutes,
        ROUND(
            CAST(COALESCE(zm.total_zone_visits, 0) AS FLOAT) /
            CAST(CASE WHEN COALESCE(zm.active_days, 1) > 1 THEN zm.active_days ELSE 1 END AS FLOAT),
            2
        ) AS daily_avg_footfall,
        ROUND(CAST(COALESCE(zm.total_zone_visits, 0) AS FLOAT) / CAST(z.area_sq_km AS FLOAT), 2) AS visits_per_sq_km,
        DENSE_RANK() OVER (ORDER BY COALESCE(zm.total_zone_visits, 0) DESC) AS zone_vitality_rank
    FROM zones z
    LEFT JOIN zone_store_counts sc
        ON z.zone_id = sc.zone_id
    LEFT JOIN zone_metrics zm
        ON z.zone_id = zm.zone_id
)

SELECT * FROM compiled
ORDER BY zone_vitality_rank ASC
