-- Intermediate Model: int_valid_store_visits
-- Enforces business dwell thresholds (5.0 <= dwell <= 180.0 min) and attaches store metadata

WITH visits AS (
    SELECT * FROM {{ ref('stg_store_visits') }}
),

stores AS (
    SELECT * FROM {{ ref('stg_store_locations') }}
),

valid_visits AS (
    SELECT
        v.visit_id,
        v.user_id,
        v.store_id,
        s.store_name,
        s.store_category,
        s.is_active AS store_is_active,
        v.arrival_time,
        v.departure_time,
        v.dwell_time_minutes,
        v.observation_count,
        v.min_distance_km,
        v.visit_date,
        v.arrival_hour
    FROM visits v
    INNER JOIN stores s
        ON v.store_id = s.store_id
    WHERE v.dwell_time_minutes BETWEEN 5.0 AND 180.0
      AND s.is_active = TRUE
)

SELECT * FROM valid_visits
