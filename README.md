<<<<<<< HEAD
# GeoPulse — Hyper-Local Retail Mobility Analytics

**Domain:** Retail Strategy & Geospatial Analytics

GeoPulse is a learning prototype that uses synthetic, anonymized-style GPS pings to explore hourly footfall, store catchment areas, spatial overlap, and potential traffic cannibalization.

> **Privacy and accuracy:** Use synthetic data only at this stage. Do not upload real mobile-location data or personally identifiable information. Any cannibalization percentage must be calculated from the generated dataset and labelled as an estimate, not a real-world fact.

## Planned technology stack
- Python / PySpark — data generation and processing
- Snowflake — storage and `GEOGRAPHY` operations (when configured)
- Apache Sedona — spatial joins (when configured)
- dbt — hourly footfall transformations
- Kepler.gl — geospatial visualization
- Apache Airflow — orchestration

## Repository structure
```text
data/                 # Synthetic raw and processed datasets
notebooks/            # Exploration
src/data_generation/  # Synthetic GPS ping generation
src/data_quality/     # Schema and quality checks
src/spatial_processing/ # Spatial joins
src/analytics/        # Footfall and overlap metrics
sql/snowflake/        # Snowflake SQL
dbt/                  # dbt models
dashboard/            # Kepler.gl/dashboard assets
airflow/dags/         # Airflow DAGs
tests/                # Tests
reports/              # Findings and charts
docs/                 # Architecture and scope
```

## Milestones
1. Define schema and generate synthetic GPS pings.
2. Validate coordinates and timestamps.
3. Design Snowflake tables and load data if account access is available.
4. Implement point-in-polygon spatial joins.
5. Aggregate hourly footfall with dbt.
6. Estimate catchment overlap.
7. Visualize results with Kepler.gl.
8. Add orchestration and tests.

## Quick start
Python 3.10+ recommended.
```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

This is scaffolding only. Do not claim cloud/tool integrations until they are configured and tested.

