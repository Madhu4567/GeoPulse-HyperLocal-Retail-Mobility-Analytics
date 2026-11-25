-- Intermediate Model: int_visit_zone_mapping
-- Associates visit events with their containing commercial zones while preserving strict 1-to-1 visit grain

WITH visits AS (
    SELECT * FROM {{ ref('int_visit_time_dimensions') }}
),

store_zones AS (
    SELECT * FROM {{ ref('stg_store_zone_mapping') }}
),

joined AS (
    SELECT
        v.visit_id,
        v.user_id,
        v.store_id,
        v.store_name,
        v.store_category,
        COALESCE(sz.zone_id, 'UNZONED') AS zone_id,
        COALESCE(sz.zone_name, 'Outside Commercial Zones') AS zone_name,
        COALESCE(sz.zone_type, 'Unassigned') AS zone_type,
        COALESCE(sz.is_within_zone, FALSE) AS is_within_commercial_zone,
        v.arrival_time,
        v.departure_time,
        v.dwell_time_minutes,
        v.visit_date,
        v.arrival_hour,
        v.day_of_week_name,
        v.day_of_week_num,
        v.is_weekend,
        v.daypart_bucket
    FROM visits v
    LEFT JOIN store_zones sz
        ON v.store_id = sz.store_id
)

SELECT * FROM joined
