# GeoPulse — Non-Functional Requirements

> **Document**: Non-Functional Requirements Specification  
> **Project**: GeoPulse — Hyper-Local Retail Mobility Analytics  
> **Phase**: Phase 1 — Day 1  
> **Last Updated**: 2026-11-17  

---

## 1. Performance Requirements

| ID | Requirement | Metric / Target | Verification Method |
|---|---|---|---|
| **NFR-PERF-01** | GPS Batch Processing Time | Process 250,000 raw GPS records through cleaning, Haversine, and nearest store mapping in < 5 minutes on standard local compute (4 CPU cores, 8GB RAM). | Benchmark execution logs. |
| **NFR-PERF-02** | Haversine Vectorization | Haversine distance calculations must use vectorized NumPy or spatial indexing, avoiding nested Python iterations ($O(N \times M)$ naive loops). | Code inspection and execution profiling. |
| **NFR-PERF-03** | Query Response Time | Analytical queries on transformed Marts in Snowflake or local parquet/DuckDB must complete in < 3 seconds for standard aggregations. | Query performance benchmarks. |
| **NFR-PERF-04** | Dashboard Load Time | Kepler.gl and Plotly visual components must render initial view in < 5 seconds with sampled or aggregated geometry (< 100,000 points). | Browser render profiling. |

---

## 2. Scalability Requirements

| ID | Requirement | Description |
|---|---|---|
| **NFR-SCAL-01** | Parameterized Data Volume | Data generation and processing scripts must accept configurable parameters (`num_users`, `num_points`, `num_stores`) allowing testing at 10k, 250k, or 1M+ scales. |
| **NFR-SCAL-02** | Distributed Processing Ready | Spatial joins and transformations must be structured to run locally on Pandas/GeoPandas or scale horizontally via Apache Sedona / PySpark. |
| **NFR-SCAL-03** | Cloud Warehouse Partitioning | Snowflake raw tables and marts must leverage date-based clustering keys (`visit_date`, `timestamp`) to prevent full table scans as dataset grows. |

---

## 3. Data Quality & Integrity Requirements

| ID | Requirement | Specification |
|---|---|---|
| **NFR-DQ-01** | Coordinate System & Bounds | All geographic coordinates must strictly adhere to WGS 84 (EPSG:4326). Latitude range: `[-90.0, 90.0]`; Longitude range: `[-180.0, 180.0]`. Out-of-bounds rows must be rejected. |
| **NFR-DQ-02** | Timestamp Formatting | Timestamps must be stored in UTC format as ISO 8601 (`YYYY-MM-DDTHH:MM:SSZ` or `TIMESTAMP_NTZ`). No future timestamps permitted. |
| **NFR-DQ-03** | Identifier Conventions | Identifiers must follow standard prefixes: `USR_` (User), `STR_` (Store), `ZN_` (Commercial Zone), `VST_` (Visit). Primary keys must be strictly unique. |
| **NFR-DQ-04** | Deduplication & Rejection | Duplicate sensor records must be isolated. Non-conforming records must be written to `data/rejected/` with rejection reasons without halting execution. |

---

## 4. Privacy, Security & Ethics

| ID | Requirement | Specification |
|---|---|---|
| **NFR-SEC-01** | Synthetic Data Only | In Phase 1 and 2 prototype stages, 100% of mobility data must be synthetically generated. No real PII (Personally Identifiable Information) or real-world individual movement trails may be stored. |
| **NFR-SEC-02** | Credential Isolation | No API keys, passwords, database credentials, or Snowflake tokens may be hardcoded or checked into Git. All credentials must be ingested from `.env` or system environment variables. |
| **NFR-SEC-03** | Aggregation for Public Visuals | Public or dashboard views must display aggregated visit counts and polygon catchments rather than granular single-user trajectory traces. |

---

## 5. Maintainability & Code Quality

| ID | Requirement | Specification |
|---|---|---|
| **NFR-MAINT-01** | PEP 8 Adherence | All Python code must conform to PEP 8 standards, utilizing clean module boundaries, descriptive naming, and standard error handling. |
| **NFR-MAINT-02** | Modularity & Single Responsibility | Generators, cleaners, spatial processors, and connectors must be isolated into dedicated classes and functions in `data_engineering/` and `src/`. |
| **NFR-MAINT-03** | Project Memory Tracking | Architectural changes, data schema modifications, and test outcomes must be documented in `AI_README.md` after every meaningful task. |

---

## 6. Testing & Reproducibility

| ID | Requirement | Specification |
|---|---|---|
| **NFR-TEST-01** | Automated Unit Tests | Critical functions (Haversine distance, coordinate validation, visit dwell calculation) must have automated tests in `tests/` with `pytest`. |
| **NFR-TEST-02** | Seeded Generation | Synthetic data generation scripts must support fixed random seeds (`random_state`) to ensure reproducibility across test runs and environments. |
