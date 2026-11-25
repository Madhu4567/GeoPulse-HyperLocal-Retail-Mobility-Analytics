-- Staging Model: stg_store_locations
-- Cleaned retail store master records with validated status and category

WITH source AS (
    SELECT * FROM {{ source('raw', 'raw_store_locations') }}
),

standardized AS (
    SELECT
        CAST(store_id AS VARCHAR) AS store_id,
        TRIM(CAST(store_name AS VARCHAR)) AS store_name,
        TRIM(CAST(store_category AS VARCHAR)) AS store_category,
        CAST(latitude AS FLOAT) AS latitude,
        CAST(longitude AS FLOAT) AS longitude,
        LOWER(TRIM(CAST(store_status AS VARCHAR))) AS store_status,
        CASE
            WHEN LOWER(TRIM(CAST(store_status AS VARCHAR))) = 'active' THEN TRUE
            ELSE FALSE
        END AS is_active
    FROM source
    WHERE store_id IS NOT NULL
      AND latitude BETWEEN -90.0 AND 90.0
      AND longitude BETWEEN -180.0 AND 180.0
)

SELECT * FROM standardized
