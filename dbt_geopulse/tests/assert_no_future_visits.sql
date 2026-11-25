-- Test: assert_no_future_visits
-- Returns visits with arrival dates in the future (> 2030) (should return 0 rows)

SELECT
    visit_id,
    arrival_time
FROM {{ ref('stg_store_visits') }}
WHERE arrival_time > '2030-01-01 00:00:00'
