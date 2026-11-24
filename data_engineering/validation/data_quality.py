"""
GeoPulse Data Quality Aggregator & Reporter
Generates comprehensive JSON audit summaries tracking input volume, valid counts,
rejections, and anomaly detection stats across datasets.
"""
from pathlib import Path
from typing import Dict, Any, Optional
import json
from datetime import datetime

import sys
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.settings import PATHS
from data_engineering.cleaning.gps_cleaner import clean_gps_mobility_data
from data_engineering.cleaning.store_cleaner import clean_store_locations_data


def generate_full_data_quality_report(
    gps_metrics: Optional[Dict[str, Any]] = None,
    store_metrics: Optional[Dict[str, Any]] = None,
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Compile overall data quality audit report and persist as JSON."""
    if gps_metrics is None:
        _, _, gps_metrics = clean_gps_mobility_data()

    if store_metrics is None:
        _, _, store_metrics = clean_store_locations_data()

    report = {
        "report_generated_at": datetime.utcnow().isoformat() + "Z",
        "pipeline_version": "1.0.0",
        "datasets": {
            "gps_mobility": gps_metrics,
            "store_locations": store_metrics,
        },
        "summary": {
            "total_records_analyzed": gps_metrics["total_input_records"] + store_metrics["total_input_records"],
            "total_valid_records": gps_metrics["valid_records"] + store_metrics["valid_records"],
            "total_rejected_records": gps_metrics["rejected_records"] + store_metrics["rejected_records"],
            "overall_rejection_rate_pct": round(
                ((gps_metrics["rejected_records"] + store_metrics["rejected_records"]) /
                 (gps_metrics["total_input_records"] + store_metrics["total_input_records"])) * 100, 2
            ),
        },
        "status": "PASS" if gps_metrics["valid_records"] > 0 and store_metrics["valid_records"] > 0 else "FAIL",
    }

    out_p = output_path or (PATHS["data_quality"] / "data_quality_report.json")
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with open(out_p, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"[DataQuality] Full report written to {out_p}")
    return report


if __name__ == "__main__":
    generate_full_data_quality_report()
