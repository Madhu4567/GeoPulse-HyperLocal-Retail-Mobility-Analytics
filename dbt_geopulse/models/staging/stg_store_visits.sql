-- Staging Model: stg_store_visits
-- Sanitized, confirmed store visit events with validated dwell durations

WITH source AS (
    SELECT * FROM {{ source('processed', 'detected_store_visits') }}
),

standardized AS (
    SELECT
        CAST(visit_id AS VARCHAR) AS visit_id,
        CAST(user_id AS VARCHAR) AS user_id,
        CAST(store_id AS VARCHAR) AS store_id,
        CAST(arrival_time AS TIMESTAMP) AS arrival_time,
        CAST(departure_time AS TIMESTAMP) AS departure_time,
        CAST(dwell_time_minutes AS FLOAT) AS dwell_time_minutes,
        CAST(observation_count AS INTEGER) AS observation_count,
        CAST(min_distance_km AS FLOAT) AS min_distance_km,
        CAST(visit_date AS DATE) AS visit_date,
        CAST(SUBSTR(CAST(arrival_time AS VARCHAR), 12, 2) AS INTEGER) AS arrival_hour
    FROM source
    WHERE visit_id IS NOT NULL
      AND dwell_time_minutes > 0.0
)

SELECT * FROM standardized
