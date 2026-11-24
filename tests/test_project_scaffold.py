"""Tests for project directory scaffold."""
from pathlib import Path
import unittest


class TestProjectScaffold(unittest.TestCase):
    def test_expected_project_directories_exist(self):
        root = Path(__file__).resolve().parents[1]
        expected_dirs = [
            "data",
            "data_engineering",
            "src",
            "sql",
            "dbt",
            "dashboard",
            "airflow",
            "tests",
            "docs",
            "documentation",
            "config",
            "snowflake",
        ]
        for folder in expected_dirs:
            folder_path = root / folder
            self.assertTrue(folder_path.is_dir(), f"Required folder '{folder}' is missing.")


if __name__ == "__main__":
    unittest.main()
