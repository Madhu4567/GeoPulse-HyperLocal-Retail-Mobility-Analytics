"""Integration tests for dbt SQL models and analytical transformations."""
import unittest
from pathlib import Path
import pandas as pd

from dbt_geopulse.local_runner import DbtLocalRunner


class TestDbtAnalytics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = DbtLocalRunner()
        cls.model_results = cls.runner.execute_all_models()
        cls.test_results = cls.runner.run_tests()

    def test_all_models_execute_successfully(self):
        expected_models = [
            "stg_gps_mobility",
            "stg_store_locations",
            "stg_store_visits",
            "stg_commercial_zones",
            "stg_store_zone_mapping",
            "int_valid_store_visits",
            "int_visit_time_dimensions",
            "int_visit_zone_mapping",
            "int_store_footfall_base",
            "mart_store_footfall",
            "mart_hourly_footfall",
            "mart_daily_footfall",
            "mart_zone_footfall",
            "mart_store_performance",
        ]
        for m in expected_models:
            self.assertIn(m, self.model_results)
            self.assertEqual(self.model_results[m]["status"], "SUCCESS")
            self.assertGreater(self.model_results[m]["rows"], 0)

    def test_dbt_custom_assertions_pass(self):
        self.assertTrue(self.test_results["all_tests_passed"])
        self.assertEqual(self.test_results["failed_count"], 0)

    def test_mart_store_footfall_grain_and_metrics(self):
        df = pd.read_csv(self.runner.output_dir / "mart_store_footfall.csv")
        self.assertEqual(df["store_id"].nunique(), len(df))  # Unique grain
        self.assertTrue((df["total_visits"] >= df["unique_visitors"]).all())
        self.assertTrue((df["avg_dwell_time_minutes"] > 0).all())

    def test_mart_zone_footfall_conservation(self):
        df = pd.read_csv(self.runner.output_dir / "mart_zone_footfall.csv")
        self.assertEqual(len(df), 6)
        self.assertEqual(df["zone_id"].nunique(), 6)
        self.assertTrue((df["visits_per_sq_km"] >= 0).all())

    def test_mart_store_performance_rankings(self):
        df = pd.read_csv(self.runner.output_dir / "mart_store_performance.csv")
        self.assertEqual(df.iloc[0]["portfolio_rank"], 1)
        self.assertTrue((df["repeat_visitor_rate_pct"].between(0.0, 100.0)).all())


if __name__ == "__main__":
    unittest.main()
