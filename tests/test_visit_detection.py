"""Unit tests for visit detection engine."""
import unittest
import pandas as pd
from datetime import datetime, timedelta

from data_engineering.spatial.visit_detection import StoreVisitDetector


class TestVisitDetection(unittest.TestCase):
    def test_visit_detection_within_radius_and_dwell(self):
        # 4 consecutive observations at the same store over 20 minutes (within 0.03 km)
        base_time = datetime(2026, 11, 1, 12, 0, 0)
        pings = []
        for i in range(4):
            pings.append({
                "user_id": "USR_TEST",
                "nearest_store_id": "STR_001",
                "timestamp": (base_time + timedelta(minutes=i * 6)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "distance_km": 0.02,
            })

        # Add single transient ping at another store (should be ignored due to < 2 obs)
        pings.append({
            "user_id": "USR_TEST",
            "nearest_store_id": "STR_002",
            "timestamp": "2026-11-01T14:00:00Z",
            "distance_km": 0.01,
        })

        mapped_df = pd.DataFrame(pings)
        detector = StoreVisitDetector(
            visit_radius_km=0.05,
            min_dwell_minutes=5.0,
            min_observations=2,
        )

        visits_df, metrics = detector.detect_visits(mapped_df)

        self.assertEqual(len(visits_df), 1)
        self.assertEqual(visits_df.iloc[0]["store_id"], "STR_001")
        self.assertEqual(visits_df.iloc[0]["user_id"], "USR_TEST")
        self.assertEqual(visits_df.iloc[0]["observation_count"], 4)
        self.assertAlmostEqual(visits_df.iloc[0]["dwell_time_minutes"], 18.0, delta=1.0)
        self.assertEqual(metrics["total_visits_detected"], 1)


if __name__ == "__main__":
    unittest.main()
