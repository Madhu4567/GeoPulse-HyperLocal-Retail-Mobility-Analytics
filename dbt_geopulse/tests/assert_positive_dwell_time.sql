-- Test: assert_positive_dwell_time
-- Returns records where dwell time is <= 0 minutes (should return 0 rows for test to pass)

SELECT
    visit_id,
    dwell_time_minutes
FROM {{ ref('stg_store_visits') }}
WHERE dwell_time_minutes <= 0.0
