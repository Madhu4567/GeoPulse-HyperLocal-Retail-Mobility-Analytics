-- Staging Model: stg_commercial_zones
-- Validated commercial geographic zones and boundary metadata

WITH source AS (
    SELECT * FROM {{ source('reference', 'commercial_zones') }}
),

standardized AS (
    SELECT
        CAST(zone_id AS VARCHAR) AS zone_id,
        TRIM(CAST(zone_name AS VARCHAR)) AS zone_name,
        TRIM(CAST(zone_type AS VARCHAR)) AS zone_type,
        CAST(geometry AS VARCHAR) AS geometry_wkt,
        CAST(area_sq_km AS FLOAT) AS area_sq_km,
        CAST(created_at AS TIMESTAMP) AS created_at
    FROM source
    WHERE zone_id IS NOT NULL
)

SELECT * FROM standardized
