-- Staging Model: stg_store_zone_mapping
-- Spatial point-in-polygon assignment between retail stores and commercial zones

WITH source AS (
    SELECT * FROM {{ source('processed', 'store_zone_mapping') }}
),

standardized AS (
    SELECT
        CAST(store_id AS VARCHAR) AS store_id,
        TRIM(CAST(store_name AS VARCHAR)) AS store_name,
        TRIM(CAST(store_category AS VARCHAR)) AS store_category,
        CAST(latitude AS FLOAT) AS latitude,
        CAST(longitude AS FLOAT) AS longitude,
        CAST(zone_id AS VARCHAR) AS zone_id,
        TRIM(CAST(zone_name AS VARCHAR)) AS zone_name,
        TRIM(CAST(zone_type AS VARCHAR)) AS zone_type,
        CASE
            WHEN is_within_zone = 1 OR is_within_zone = TRUE OR is_within_zone = 'True' THEN TRUE
            ELSE FALSE
        END AS is_within_zone
    FROM source
    WHERE store_id IS NOT NULL
)

SELECT * FROM standardized
