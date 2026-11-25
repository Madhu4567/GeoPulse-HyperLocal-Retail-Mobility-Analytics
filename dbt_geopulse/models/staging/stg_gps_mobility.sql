-- Staging Model: stg_gps_mobility
-- Cleaned, typed GPS sensor observations conforming to WGS84 coordinates

WITH source AS (
    SELECT * FROM {{ source('raw', 'raw_gps_mobility') }}
),

cleaned AS (
    SELECT
        CAST(user_id AS VARCHAR) AS user_id,
        CAST(timestamp AS TIMESTAMP) AS observed_at,
        CAST(latitude AS FLOAT) AS latitude,
        CAST(longitude AS FLOAT) AS longitude,
        CAST(accuracy AS FLOAT) AS accuracy_meters,
        CAST(location_id AS VARCHAR) AS location_id,
        DATE(CAST(timestamp AS TIMESTAMP)) AS observation_date,
        CAST(SUBSTR(CAST(timestamp AS VARCHAR), 12, 2) AS INTEGER) AS observation_hour
    FROM source
    WHERE user_id IS NOT NULL
      AND latitude BETWEEN -90.0 AND 90.0
      AND longitude BETWEEN -180.0 AND 180.0
)

SELECT * FROM cleaned
