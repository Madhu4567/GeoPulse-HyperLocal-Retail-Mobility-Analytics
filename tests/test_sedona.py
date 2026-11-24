"""Unit tests for spatial processing and consistency checks."""
import unittest
import pandas as pd

from data_engineering.spatial.sedona_processor import SedonaSpatialProcessor


class TestSedonaProcessor(unittest.TestCase):
    def test_spatial_proximity_join(self):
        gps_df = pd.DataFrame([
            {"user_id": "USR_01", "timestamp": "2026-11-01T10:00:00Z", "latitude": 40.758000, "longitude": -73.985500},
            {"user_id": "USR_02", "timestamp": "2026-11-01T10:00:00Z", "latitude": 40.710000, "longitude": -74.000000},
        ])

        stores_df = pd.DataFrame([
            {"store_id": "STR_A", "store_name": "Store Near USR 01", "store_category": "Grocery", "latitude": 40.758050, "longitude": -73.985550, "store_status": "active"},
            {"store_id": "STR_B", "store_name": "Store Far Away", "store_category": "Electronics", "latitude": 40.790000, "longitude": -73.950000, "store_status": "active"},
        ])

        processor = SedonaSpatialProcessor(proximity_radius_meters=50.0)
        enriched_gps, spatial_join_df, summary = processor.process_spatial_proximity(gps_df, stores_df)

        self.assertIn("geometry_wkt", enriched_gps.columns)
        self.assertTrue(enriched_gps.iloc[0]["geometry_wkt"].startswith("POINT(-73.9855"))
        self.assertEqual(len(spatial_join_df), 1)
        self.assertEqual(spatial_join_df.iloc[0]["store_id"], "STR_A")
        self.assertTrue(summary["haversine_vs_spatial_join_validation"]["consistency_verified"])


if __name__ == "__main__":
    unittest.main()
