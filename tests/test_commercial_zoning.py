"""Unit and integration tests for commercial zoning modules."""
import unittest
import pandas as pd
from pathlib import Path

from analytics.commercial_zoning.zone_validator import (
    geodesic_polygon_area_sq_km,
    point_in_polygon,
    CommercialZoneValidator,
)
from analytics.commercial_zoning.zone_generator import CommercialZoneGenerator
from analytics.commercial_zoning.store_zone_mapping import StoreZoneMapper
from analytics.commercial_zoning.visit_zone_mapping import VisitZoneMapper
from analytics.commercial_zoning.zone_summary import CommercialZoneSummarizer


class TestCommercialZoning(unittest.TestCase):
    def test_geodesic_polygon_area_calculation(self):
        # 0.01 deg x 0.01 deg near 40N is approx 1.11 km x 0.85 km ~ 0.94 sq km
        square_coords = [
            (40.70, -74.00),
            (40.71, -74.00),
            (40.71, -73.99),
            (40.70, -73.99),
            (40.70, -74.00),
        ]
        area = geodesic_polygon_area_sq_km(square_coords)
        self.assertGreater(area, 0.8)
        self.assertLess(area, 1.2)

    def test_point_in_polygon_containment(self):
        polygon = [
            (40.70, -74.00),
            (40.72, -74.00),
            (40.72, -73.98),
            (40.70, -73.98),
            (40.70, -74.00),
        ]
        # Point inside
        self.assertTrue(point_in_polygon(40.71, -73.99, polygon))
        # Point outside
        self.assertFalse(point_in_polygon(40.73, -73.99, polygon))
        self.assertFalse(point_in_polygon(40.71, -73.97, polygon))

    def test_zone_generator_and_validator(self):
        generator = CommercialZoneGenerator()
        df, geojson = generator.generate()

        self.assertEqual(len(df), 6)
        self.assertIn("zone_id", df.columns)
        self.assertIn("geometry", df.columns)
        self.assertIn("area_sq_km", df.columns)
        self.assertTrue((df["area_sq_km"] > 0.0).all())
        self.assertEqual(len(geojson["features"]), 6)

    def test_store_zone_mapping_preserves_unmatched(self):
        sample_stores = pd.DataFrame([
            {"store_id": "STR_IN", "store_name": "Midtown Shop", "store_category": "Fashion", "latitude": 40.7505, "longitude": -73.9890, "store_status": "active"},
            {"store_id": "STR_OUT", "store_name": "Remote Shop", "store_category": "Grocery", "latitude": 40.8100, "longitude": -73.9400, "store_status": "active"},
        ])

        mapper = StoreZoneMapper()
        mapped_df, summary = mapper.map_stores(sample_stores)

        self.assertEqual(len(mapped_df), 2)
        # Store in Midtown should match ZN_001
        in_row = mapped_df[mapped_df["store_id"] == "STR_IN"].iloc[0]
        self.assertEqual(in_row["zone_id"], "ZN_001")
        self.assertTrue(in_row["is_within_zone"])

        # Store far north should be UNZONED but preserved
        out_row = mapped_df[mapped_df["store_id"] == "STR_OUT"].iloc[0]
        self.assertEqual(out_row["zone_id"], "UNZONED")
        self.assertFalse(out_row["is_within_zone"])

    def test_visit_zone_mapping_strict_grain(self):
        sample_visits = pd.DataFrame([
            {"visit_id": "VST_01", "user_id": "USR_1", "store_id": "STR_01", "arrival_time": "2026-11-01T10:00:00Z", "departure_time": "2026-11-01T10:20:00Z", "dwell_time_minutes": 20.0, "observation_count": 3, "min_distance_km": 0.01, "visit_date": "2026-11-01"},
            {"visit_id": "VST_02", "user_id": "USR_2", "store_id": "STR_01", "arrival_time": "2026-11-01T11:00:00Z", "departure_time": "2026-11-01T11:30:00Z", "dwell_time_minutes": 30.0, "observation_count": 4, "min_distance_km": 0.02, "visit_date": "2026-11-01"},
        ])

        sample_store_zone = pd.DataFrame([
            {"store_id": "STR_01", "store_name": "Test Store", "store_category": "Fashion", "latitude": 40.75, "longitude": -73.98, "store_status": "active", "zone_id": "ZN_001", "zone_name": "Midtown", "zone_type": "Shopping District", "is_within_zone": True}
        ])

        mapper = VisitZoneMapper()
        vz_df, summary = mapper.map_visits(sample_visits, sample_store_zone)

        self.assertEqual(len(vz_df), 2)
        self.assertEqual(vz_df["visit_id"].nunique(), 2)
        self.assertTrue((vz_df["zone_id"] == "ZN_001").all())


if __name__ == "__main__":
    unittest.main()
