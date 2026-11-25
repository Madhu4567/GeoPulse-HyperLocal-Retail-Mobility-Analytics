-- Intermediate Model: int_visit_time_dimensions
-- Enriches validated visits with temporal calendar attributes, weekend flags, and daypart buckets

WITH visits AS (
    SELECT * FROM {{ ref('int_valid_store_visits') }}
),

time_dimensions AS (
    SELECT
        visit_id,
        user_id,
        store_id,
        store_name,
        store_category,
        arrival_time,
        departure_time,
        dwell_time_minutes,
        visit_date,
        arrival_hour,
        -- Day of week name derivation
        CASE CAST(STRFTIME('%w', visit_date) AS INTEGER)
            WHEN 0 THEN 'Sunday'
            WHEN 1 THEN 'Monday'
            WHEN 2 THEN 'Tuesday'
            WHEN 3 THEN 'Wednesday'
            WHEN 4 THEN 'Thursday'
            WHEN 5 THEN 'Friday'
            WHEN 6 THEN 'Saturday'
            ELSE 'Unknown'
        END AS day_of_week_name,
        CAST(STRFTIME('%w', visit_date) AS INTEGER) AS day_of_week_num,
        -- Weekend classification
        CASE
            WHEN CAST(STRFTIME('%w', visit_date) AS INTEGER) IN (0, 6) THEN TRUE
            ELSE FALSE
        END AS is_weekend,
        -- Daypart classification
        CASE
            WHEN arrival_hour BETWEEN 6 AND 11 THEN 'Morning'
            WHEN arrival_hour BETWEEN 12 AND 16 THEN 'Afternoon'
            WHEN arrival_hour BETWEEN 17 AND 21 THEN 'Evening'
            ELSE 'Night'
        END AS daypart_bucket
    FROM visits
)

SELECT * FROM time_dimensions
