"""Unit tests for nearest-store mapping engine."""
import unittest
import pandas as pd
import numpy as np

from data_engineering.spatial.nearest_store import NearestStoreMapper


class TestNearestStoreMapper(unittest.TestCase):
    def test_nearest_store_selection(self):
        gps_df = pd.DataFrame([
            {"user_id": "USR_01", "timestamp": "2026-11-01T10:00:00Z", "latitude": 40.7580, "longitude": -73.9855},
            {"user_id": "USR_02", "timestamp": "2026-11-01T10:00:00Z", "latitude": 40.7000, "longitude": -74.0100},
        ])

        stores_df = pd.DataFrame([
            {"store_id": "STR_MIDTOWN", "store_name": "Midtown Store", "store_category": "Fashion", "latitude": 40.7581, "longitude": -73.9856, "store_status": "active"},
            {"store_id": "STR_DOWNTOWN", "store_name": "Downtown Store", "store_category": "Grocery", "latitude": 40.7002, "longitude": -74.0098, "store_status": "active"},
        ])

        mapper = NearestStoreMapper(max_threshold_km=5.0)
        result_df, metrics = mapper.map_nearest(gps_df, stores_df)

        self.assertEqual(len(result_df), 2)
        # USR_01 should map to STR_MIDTOWN
        self.assertEqual(result_df.loc[0, "nearest_store_id"], "STR_MIDTOWN")
        self.assertLess(result_df.loc[0, "distance_km"], 0.05)

        # USR_02 should map to STR_DOWNTOWN
        self.assertEqual(result_df.loc[1, "nearest_store_id"], "STR_DOWNTOWN")
        self.assertLess(result_df.loc[1, "distance_km"], 0.05)

        self.assertTrue(result_df["within_distance_threshold"].all())


if __name__ == "__main__":
    unittest.main()
