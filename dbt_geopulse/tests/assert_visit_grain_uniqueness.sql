-- Test: assert_visit_grain_uniqueness
-- Checks that visit_id is not duplicated in int_visit_zone_mapping (should return 0 rows)

SELECT
    visit_id,
    COUNT(*) AS record_count
FROM {{ ref('int_visit_zone_mapping') }}
GROUP BY visit_id
HAVING COUNT(*) > 1
