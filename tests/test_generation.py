"""Unit tests for synthetic data generation."""
import unittest
import pandas as pd
import numpy as np

from data_engineering.generation.store_generator import StoreDataGenerator
from data_engineering.generation.gps_generator import GPSDataGenerator
from config.settings import DATA_CONFIG


class TestDataGeneration(unittest.TestCase):
    def test_store_generation_schema_and_bounds(self):
        generator = StoreDataGenerator(num_stores=15, random_seed=42)
        df = generator.generate()

        self.assertEqual(len(df), 15)
        expected_cols = {"store_id", "store_name", "store_category", "latitude", "longitude", "store_status"}
        self.assertTrue(expected_cols.issubset(set(df.columns)))

        # Unique IDs
        self.assertEqual(df["store_id"].nunique(), 15)
        self.assertTrue(all(s.startswith("STR_") for s in df["store_id"]))

        # Valid coordinates within study area
        self.assertTrue(df["latitude"].between(DATA_CONFIG["lat_min"] - 0.05, DATA_CONFIG["lat_max"] + 0.05).all())
        self.assertTrue(df["longitude"].between(DATA_CONFIG["lon_min"] - 0.05, DATA_CONFIG["lon_max"] + 0.05).all())

    def test_gps_generation_and_anomalies(self):
        generator = GPSDataGenerator(num_users=10, target_pings=100, random_seed=42, anomaly_rate=0.05)
        df, summary = generator.generate()

        self.assertGreaterEqual(len(df), 50)
        self.assertEqual(summary["unique_users"], 10)
        self.assertIn("injected_anomalies", summary)
        self.assertGreater(summary["total_anomalies"], 0)


if __name__ == "__main__":
    unittest.main()
