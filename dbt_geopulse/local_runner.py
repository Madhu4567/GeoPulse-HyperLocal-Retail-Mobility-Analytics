"""
GeoPulse Local dbt SQL Execution & Validation Runner
Executes dbt SQL models and data quality tests directly against local processed datasets
using in-memory SQL execution, generating certified analytics mart outputs.
"""
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import sqlite3
import pandas as pd
import json
import re

import sys
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.settings import PATHS


class DbtLocalRunner:
    """Simulates dbt execution engine locally, parsing and running models in topological order."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or (PATHS["data_processed"] / "marts")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.create_function("GREATEST", -1, max)
        self.conn.create_function("LEAST", -1, min)
        self._load_sources()

    def _load_sources(self) -> None:
        """Load Phase 2 and commercial zoning CSVs into source tables."""
        sources = {
            "raw_gps_mobility": PATHS["data_raw"] / "gps_mobility.csv",
            "raw_store_locations": PATHS["data_reference"] / "store_locations.csv",
            "cleaned_gps_mobility": PATHS["data_processed"] / "cleaned_gps_mobility.csv",
            "cleaned_store_locations": PATHS["data_processed"] / "cleaned_store_locations.csv",
            "detected_store_visits": PATHS["data_processed"] / "detected_store_visits.csv",
            "commercial_zones": PATHS["data_reference"] / "commercial_zones.csv",
            "store_zone_mapping": PATHS["data_processed"] / "store_zone_mapping.csv",
        }

        for table_name, file_path in sources.items():
            if not file_path.exists():
                raise FileNotFoundError(f"Source file {file_path} not found. Complete prior pipeline steps first.")
            df = pd.read_csv(file_path)
            df.to_sql(table_name, self.conn, if_exists="replace", index=False)

    def _clean_sql(self, sql_content: str) -> str:
        """Strip dbt Jinja tags ({{ ref(...) }}, {{ source(...) }}) into SQL table identifiers."""
        # Replace {{ source('...', 'table_name') }} with table_name
        sql = re.sub(r"\{\{\s*source\s*\(\s*['\"][^'\"]+['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)\s*\}\}", r"\1", sql_content)
        # Replace {{ ref('model_name') }} with model_name
        sql = re.sub(r"\{\{\s*ref\s*\(\s*['\"]([^'\"]+)['\"]\s*\)\s*\}\}", r"\1", sql)
        # Strip other jinja comments or tags
        sql = re.sub(r"\{%.*?%\}", "", sql)
        sql = re.sub(r"\{#.*?#\}", "", sql)
        return sql.strip()

    def run_model(self, model_name: str, sql_path: Path) -> pd.DataFrame:
        """Execute a model SQL script and save as a view/table in memory."""
        raw_sql = sql_path.read_text(encoding="utf-8")
        clean_sql = self._clean_sql(raw_sql)

        # Create table/view
        create_sql = f"CREATE TABLE {model_name} AS {clean_sql}"
        try:
            self.conn.execute(f"DROP TABLE IF EXISTS {model_name}")
            self.conn.execute(create_sql)
            df = pd.read_sql_query(f"SELECT * FROM {model_name}", self.conn)
            return df
        except Exception as e:
            raise RuntimeError(f"Error executing dbt model '{model_name}': {str(e)}\nSQL:\n{clean_sql}")

    def execute_all_models(self) -> Dict[str, Any]:
        """Execute all staging, intermediate, and marts models in dependency order."""
        models_dir = ROOT_DIR / "dbt_geopulse" / "models"
        execution_order = [
            # Staging
            ("stg_gps_mobility", models_dir / "staging" / "stg_gps_mobility.sql"),
            ("stg_store_locations", models_dir / "staging" / "stg_store_locations.sql"),
            ("stg_store_visits", models_dir / "staging" / "stg_store_visits.sql"),
            ("stg_commercial_zones", models_dir / "staging" / "stg_commercial_zones.sql"),
            ("stg_store_zone_mapping", models_dir / "staging" / "stg_store_zone_mapping.sql"),
            # Intermediate
            ("int_valid_store_visits", models_dir / "intermediate" / "int_valid_store_visits.sql"),
            ("int_visit_time_dimensions", models_dir / "intermediate" / "int_visit_time_dimensions.sql"),
            ("int_visit_zone_mapping", models_dir / "intermediate" / "int_visit_zone_mapping.sql"),
            ("int_store_footfall_base", models_dir / "intermediate" / "int_store_footfall_base.sql"),
            # Marts
            ("mart_store_footfall", models_dir / "marts" / "mart_store_footfall.sql"),
            ("mart_hourly_footfall", models_dir / "marts" / "mart_hourly_footfall.sql"),
            ("mart_daily_footfall", models_dir / "marts" / "mart_daily_footfall.sql"),
            ("mart_zone_footfall", models_dir / "marts" / "mart_zone_footfall.sql"),
            ("mart_store_performance", models_dir / "marts" / "mart_store_performance.sql"),
        ]

        model_results = {}
        for name, path in execution_order:
            df = self.run_model(name, path)
            model_results[name] = {
                "rows": len(df),
                "columns": list(df.columns),
                "status": "SUCCESS",
            }
            # Save marts to disk
            if name.startswith("mart_"):
                out_csv = self.output_dir / f"{name}.csv"
                df.to_csv(out_csv, index=False)
                model_results[name]["saved_path"] = str(out_csv)

        return model_results

    def run_tests(self) -> Dict[str, Any]:
        """Execute generic and custom test assertions."""
        tests_dir = ROOT_DIR / "dbt_geopulse" / "tests"
        test_files = list(tests_dir.glob("*.sql"))

        test_results = []
        all_passed = True

        for tpath in test_files:
            tname = tpath.stem
            raw_sql = tpath.read_text(encoding="utf-8")
            clean_sql = self._clean_sql(raw_sql)
            try:
                res = pd.read_sql_query(clean_sql, self.conn)
                failure_count = len(res)
                passed = failure_count == 0
                if not passed:
                    all_passed = False
                test_results.append({
                    "test_name": tname,
                    "passed": passed,
                    "failing_rows": failure_count,
                })
            except Exception as e:
                all_passed = False
                test_results.append({
                    "test_name": tname,
                    "passed": False,
                    "error": str(e),
                })

        return {
            "all_tests_passed": all_passed,
            "total_tests_run": len(test_results),
            "passed_count": sum(1 for t in test_results if t["passed"]),
            "failed_count": sum(1 for t in test_results if not t["passed"]),
            "test_details": test_results,
        }


def run_local_dbt_pipeline() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    runner = DbtLocalRunner()
    model_results = runner.execute_all_models()
    test_results = runner.run_tests()

    print("[DbtLocalRunner] All 14 dbt models executed successfully:")
    for name, info in model_results.items():
        if name.startswith("mart_"):
            print(f"  - Mart: {name:25} ({info['rows']} rows) -> {info.get('saved_path')}")
        elif name.startswith("int_"):
            print(f"  - Intermediate: {name:25} ({info['rows']} rows)")
        else:
            print(f"  - Staging: {name:25} ({info['rows']} rows)")

    print(f"\n[DbtLocalRunner] Tests: {test_results['passed_count']}/{test_results['total_tests_run']} PASSED (Overall: {'PASS' if test_results['all_tests_passed'] else 'FAIL'})")
    for t in test_results["test_details"]:
        print(f"  - {t['test_name']}: {'PASS' if t['passed'] else 'FAIL'} (failing rows: {t.get('failing_rows', 0)})")

    return model_results, test_results


if __name__ == "__main__":
    run_local_dbt_pipeline()
