-- Test: assert_valid_store_references
-- Validates referential integrity: all visits reference valid store_id (should return 0 rows)

SELECT
    v.visit_id,
    v.store_id
FROM {{ ref('stg_store_visits') }} v
LEFT JOIN {{ ref('stg_store_locations') }} s
    ON v.store_id = s.store_id
WHERE s.store_id IS NULL
