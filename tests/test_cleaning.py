"""Unit tests for data cleaning and validation pipelines."""
import unittest
import pandas as pd
import numpy as np

from data_engineering.cleaning.gps_cleaner import GPSDataCleaner
from data_engineering.cleaning.store_cleaner import StoreDataCleaner


class TestDataCleaning(unittest.TestCase):
    def setUp(self):
        self.gps_cleaner = GPSDataCleaner()
        self.store_cleaner = StoreDataCleaner()

    def test_gps_cleaner_filters_invalid_records(self):
        sample_gps = pd.DataFrame([
            {"user_id": "USR_001", "timestamp": "2026-11-01T10:00:00Z", "latitude": 40.7580, "longitude": -73.9855, "accuracy": 10.0},
            {"user_id": "", "timestamp": "2026-11-01T10:05:00Z", "latitude": 40.7580, "longitude": -73.9855, "accuracy": 10.0},  # Missing user
            {"user_id": "USR_002", "timestamp": "2026-11-01T10:00:00Z", "latitude": 95.0000, "longitude": -73.9855, "accuracy": 10.0},  # Lat > 90
            {"user_id": "USR_003", "timestamp": "2026-11-01T10:00:00Z", "latitude": np.nan, "longitude": -73.9855, "accuracy": 10.0},   # NaN lat
            {"user_id": "USR_004", "timestamp": "2026-11-01T10:00:00Z", "latitude": 40.7580, "longitude": -73.9855, "accuracy": -5.0},   # Invalid acc
            {"user_id": "USR_001", "timestamp": "2026-11-01T10:00:00Z", "latitude": 40.7580, "longitude": -73.9855, "accuracy": 10.0},  # Duplicate
        ])

        clean_df, rejected_df, metrics = self.gps_cleaner.clean(sample_gps)

        self.assertEqual(len(clean_df), 1)
        self.assertEqual(clean_df.iloc[0]["user_id"], "USR_001")
        self.assertEqual(len(rejected_df), 5)
        self.assertEqual(metrics["valid_records"], 1)

    def test_store_cleaner_validates_categories_and_pks(self):
        sample_stores = pd.DataFrame([
            {"store_id": "STR_001", "store_name": "Valid Store", "store_category": "Grocery", "latitude": 40.75, "longitude": -73.98, "store_status": "active"},
            {"store_id": "STR_001", "store_name": "Duplicate ID", "store_category": "Grocery", "latitude": 40.76, "longitude": -73.97, "store_status": "active"},
            {"store_id": "STR_002", "store_name": "Bad Category", "store_category": "Aerospace", "latitude": 40.77, "longitude": -73.96, "store_status": "active"},
            {"store_id": "STR_003", "store_name": "Bad Status", "store_category": "Fashion", "latitude": 40.78, "longitude": -73.95, "store_status": "destroyed"},
        ])

        clean_df, rejected_df, metrics = self.store_cleaner.clean(sample_stores)

        self.assertEqual(len(clean_df), 1)
        self.assertEqual(clean_df.iloc[0]["store_id"], "STR_001")
        self.assertEqual(len(rejected_df), 3)


if __name__ == "__main__":
    unittest.main()
