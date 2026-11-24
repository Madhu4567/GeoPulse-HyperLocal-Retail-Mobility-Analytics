# 📍 GeoPulse — Hyper-Local Retail Mobility Analytics

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Warehouse-Snowflake-29B5E8.svg)](https://www.snowflake.com/)
[![Transformation](https://img.shields.io/badge/Transform-dbt-FF694B.svg)](https://www.getdbt.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Phase%202%20In%20Progress-orange.svg)](#)

---

## 1. Project Overview

**GeoPulse** is an end-to-end geospatial retail analytics platform designed to convert anonymized GPS mobility data, commercial zoning boundaries, and retail store footprints into actionable business intelligence.

Retail decision-makers can answer critical questions:
- **Where are our customers coming from?** (Customer origin & travel distance)
- **Which retail locations capture the highest footfall?** (Peak visit volume & dwell times)
- **What are the busiest hours and days per store?** (Hourly traffic trends)
- **What is the true geographic catchment area of each store?** (50m visit candidate & 5km catchment mapping)
- **Which stores have overlapping customer pools?** (Spatial overlap analysis)
- **Are our own stores cannibalizing each other?** (Cannibalization scoring & risk levels)
- **Where should we locate our next store?** (White-space gap analysis)

> **Privacy & Ethics Notice**: GeoPulse is currently developed using synthetic mobility observations. No real individual consumer trajectories or Personally Identifiable Information (PII) are stored or analyzed.

---

## 2. Technology Stack

| Technology | Purpose | Module Responsibility |
|---|---|---|
| **Python 3.10+** | Core programming language & data pipelines | Cross-Module |
| **Pandas & NumPy** | Data ingestion, vectorization, and data quality cleaning | Module 1 (Data Engineering) |
| **Haversine** | Great-circle geographic distance calculations | Module 1 (Data Engineering) |
| **Apache Sedona / GeoPandas** | Spatial joins, point-in-polygon & geometry operations | Module 1 (Spatial Processing) |
| **Snowflake** | Cloud data warehouse (RAW, STAGING, PROCESSED, ANALYTICS) | Module 1 / Module 2 |
| **dbt (dbt-snowflake)** | SQL-based transformations (Staging, Intermediate, Marts) | Module 2 (Analytics) |
| **Kepler.gl** | Interactive geospatial visualization dashboards | Module 2 (Analytics) |
| **Plotly** | Time-series, hourly distribution & footfall charts | Module 2 (Analytics) |
| **Apache Airflow** | Orchestration DAGs across pipelines | Module 3 (Shared) |
| **pytest** | Unit, integration, and data integrity test suite | Module 3 (Shared) |

---

## 3. High-Level Architecture & Data Flow

```
   [ Synthetic GPS Mobility ]   [ Retail Store Locations ]   [ Commercial Zones ]
               │                            │                          │
               └───────────────────┬────────┘                          │
                                   ▼                                   │
                      [ Data Cleaning & Quality ]                      │
                       (Filter out-of-bounds,                          │
                        deduplicate, ISO-8601)                         │
                                   │                                   │
                                   ▼                                   │
                      [ Haversine & Nearest Store ]                    │
                                   │                                   │
                                   ▼                                   │
                      [ Visit Detection Engine ]                       │
                       (Radius: 50m, Min dwell: 5m)                    │
                                   │                                   │
                                   ▼                                   │
                      [ Apache Sedona Spatial Join ] ◄─────────────────┘
                                   │
                                   ▼
                       [ Snowflake Data Warehouse ]
                       (RAW ➔ STAGING ➔ PROCESSED)
                                   │
                                   ▼
                       [ dbt Data Transformations ]
                       (STAGING ➔ INTERMEDIATE ➔ MARTS)
                                   │
               ┌───────────────────┼───────────────────┐
               ▼                   ▼                   ▼
       Footfall Analytics   Catchment Areas    Cannibalization Risk
               │                   │                   │
               └───────────────────┼───────────────────┘
                                   ▼
                   [ Kepler.gl & Plotly Dashboard ]
                                   │
                                   ▼
                         [ Business Insights ]
```

---

## 4. Repository Structure

```text
c:\Users\yash\geoplus\
├── data/
│   ├── raw/                  # Raw generated GPS mobility & store files
│   ├── processed/            # Cleaned, nearest-store, and detected visit datasets
│   ├── reference/            # Store locations, commercial zone boundaries
│   ├── rejected/             # Rejected records with audit logs
│   └── quality/              # Data quality audit reports (JSON/markdown)
├── data_engineering/
│   ├── generation/           # GPS and store synthetic data generators
│   ├── cleaning/             # Data cleaning and schema validation
│   ├── spatial/              # Haversine, nearest-store, visit detection, Sedona
│   └── validation/           # Data quality metric reporters
├── src/                      # Scaffold package references
│   ├── data_generation/
│   ├── data_quality/
│   ├── spatial_processing/
│   └── analytics/
├── snowflake/                # Snowflake connection logic, DDL schemas, and loaders
├── dbt_geopulse/             # dbt transformation models (staging, intermediate, marts)
├── airflow/
│   └── dags/                 # Airflow pipeline DAGs
├── dashboard/                # Kepler.gl and Plotly visual interfaces
├── documentation/            # Complete Phase 1 & 2 architecture & contract docs
├── config/                   # Centralized configuration (settings.py)
├── tests/                    # Pytest test suite
├── AI_README.md              # AI Project Memory & Development History
├── README.md                 # User & developer facing documentation
└── requirements.txt          # Python dependencies
```

---

## 5. Quick Start & Setup

### Prerequisites
- Python 3.10 or higher
- Git

### Installation
```powershell
# 1. Clone repository & enter folder
cd c:\Users\yash\geoplus

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env
```

---

## 6. Execution Guide

```powershell
# Run Unit Tests
pytest tests/ -v
```

---

## 7. Documentation Index

- [Project Overview](documentation/project_overview.md)
- [Functional Requirements](documentation/functional_requirements.md)
- [Non-Functional Requirements](documentation/non_functional_requirements.md)
- [System Architecture](documentation/system_architecture.md)
- [Data Flow Diagram](documentation/data_flow.md)
- [Module Design](documentation/module_design.md)
- [Database & Schema Design](documentation/database_design.md)
- [Data Dictionary](documentation/data_dictionary.md)
- [Data Contracts](documentation/data_contracts.md)
- [Snowflake Schema DDL](documentation/sql/snowflake_schema.sql)

---

## 8. License & Team
Developed under MIT License for GeoPulse Mobility Analytics.
