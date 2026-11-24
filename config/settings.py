"""
GeoPulse Global Configuration Settings
Centralized parameter management for data generation, spatial processing, and cloud warehouse.
"""
from pathlib import Path
import os

# Base Directory Resolution
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file if dotenv is available or parse simply
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

# Application Configuration
APP_CONFIG = {
    "app_name": "GeoPulse",
    "version": "1.0.0",
    "env": os.getenv("APP_ENV", "development"),
    "log_level": os.getenv("LOG_LEVEL", "INFO"),
}

# Snowflake Cloud Data Warehouse Config
SNOWFLAKE_CONFIG = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT", ""),
    "user": os.getenv("SNOWFLAKE_USER", ""),
    "password": os.getenv("SNOWFLAKE_PASSWORD", ""),
    "database": os.getenv("SNOWFLAKE_DATABASE", "GEOPULSE_DB"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "GEOPULSE_WH"),
    "schemas": {
        "raw": os.getenv("SNOWFLAKE_SCHEMA_RAW", "RAW"),
        "staging": os.getenv("SNOWFLAKE_SCHEMA_STAGING", "STAGING"),
        "processed": os.getenv("SNOWFLAKE_SCHEMA_PROCESSED", "PROCESSED"),
        "analytics": os.getenv("SNOWFLAKE_SCHEMA_ANALYTICS", "ANALYTICS"),
    },
    "role": os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
}

# Study Area & Data Generation Parameters (Default Study Area: Manhattan, NYC Core)
DATA_CONFIG = {
    "study_area_name": "New York City Core (Manhattan)",
    "city_center_lat": 40.7580,  # Midtown Manhattan
    "city_center_lon": -73.9855,
    "lat_min": 40.7000,
    "lat_max": 40.8200,
    "lon_min": -74.0200,
    "lon_max": -73.9300,
    "default_num_users": 500,
    "default_num_pings": 25000,
    "default_num_stores": 30,
    "random_seed": 42,
    "date_start": "2026-11-01T08:00:00Z",
    "date_end": "2026-11-07T22:00:00Z",
    "store_categories": [
        "Grocery",
        "Fashion",
        "Electronics",
        "Pharmacy",
        "Convenience",
        "Department Store",
        "Cafe & Bakery",
    ],
    "store_statuses": ["active", "active", "active", "active", "inactive"],
}

# Spatial Processing & Visit Detection Parameters
SPATIAL_CONFIG = {
    "crs": "EPSG:4326",  # WGS 84
    "haversine_unit": "km",
    "nearest_store_max_distance_km": 5.0,  # Max radius to associate with nearest store
    "store_visit_radius_km": 0.05,        # 50 meters for proximity visit candidate
    "min_dwell_time_minutes": 5.0,        # Minimum dwell time to constitute a visit
    "max_dwell_time_minutes": 180.0,      # Maximum dwell time cap (3 hours)
    "min_observations_per_visit": 2,      # Minimum consecutive pings in radius
    "catchment_radius_km": 5.0,           # General catchment extent
}

# Directory Paths
PATHS = {
    "base": BASE_DIR,
    "data_raw": BASE_DIR / "data" / "raw",
    "data_processed": BASE_DIR / "data" / "processed",
    "data_reference": BASE_DIR / "data" / "reference",
    "data_rejected": BASE_DIR / "data" / "rejected",
    "data_quality": BASE_DIR / "data" / "quality",
    "docs": BASE_DIR / "documentation",
    "sql": BASE_DIR / "sql",
    "tests": BASE_DIR / "tests",
}
