"""Scaffold compatibility wrapper for GPS generator."""
from data_engineering.generation.gps_generator import (
    GPSDataGenerator,
    generate_synthetic_gps_data,
)

__all__ = ["GPSDataGenerator", "generate_synthetic_gps_data"]

if __name__ == "__main__":
    generate_synthetic_gps_data()
