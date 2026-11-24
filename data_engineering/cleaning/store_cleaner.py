"""
GeoPulse Retail Store Data Cleaner & Validator
Validates store locations, checks primary key uniqueness, coordinate bounds,
and categoric consistency.
"""
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

import sys
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.settings import DATA_CONFIG, PATHS


class StoreDataCleaner:
    """Validates and cleans retail store location reference data."""

    def __init__(self, allowed_categories: Optional[List[str]] = None):
        self.allowed_categories = allowed_categories or DATA_CONFIG["store_categories"]

    def clean(self, df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """Validate raw store locations."""
        df = df_raw.copy()
        total_input = len(df)

        rejected_rows: List[Dict[str, Any]] = []
        valid_indices: List[int] = []

        rejection_counts = {
            "missing_store_id": 0,
            "duplicate_store_id": 0,
            "missing_store_name": 0,
            "missing_latitude": 0,
            "missing_longitude": 0,
            "invalid_latitude": 0,
            "invalid_longitude": 0,
            "invalid_category": 0,
            "invalid_status": 0,
            "duplicate_location": 0,
        }

        seen_store_ids = set()
        seen_coordinates = set()

        for idx, row in df.iterrows():
            reasons = []

            # Check store_id
            sid = row.get("store_id")
            if pd.isna(sid) or str(sid).strip() == "":
                reasons.append("missing_store_id")
            elif sid in seen_store_ids:
                reasons.append("duplicate_store_id")
            else:
                seen_store_ids.add(sid)

            # Check store_name
            sname = row.get("store_name")
            if pd.isna(sname) or str(sname).strip() == "":
                reasons.append("missing_store_name")

            # Check latitude
            lat = row.get("latitude")
            if pd.isna(lat):
                reasons.append("missing_latitude")
            else:
                try:
                    lat_f = float(lat)
                    if lat_f < -90.0 or lat_f > 90.0:
                        reasons.append("invalid_latitude")
                except (ValueError, TypeError):
                    reasons.append("invalid_latitude")

            # Check longitude
            lon = row.get("longitude")
            if pd.isna(lon):
                reasons.append("missing_longitude")
            else:
                try:
                    lon_f = float(lon)
                    if lon_f < -180.0 or lon_f > 180.0:
                        reasons.append("invalid_longitude")
                except (ValueError, TypeError):
                    reasons.append("invalid_longitude")

            # Check duplicate exact coordinate pair
            if not pd.isna(lat) and not pd.isna(lon):
                coord_key = (round(float(lat), 6), round(float(lon), 6))
                if coord_key in seen_coordinates:
                    reasons.append("duplicate_location")
                else:
                    seen_coordinates.add(coord_key)

            # Check store category
            cat = row.get("store_category")
            if pd.isna(cat) or cat not in self.allowed_categories:
                reasons.append("invalid_category")

            # Check store status
            status = row.get("store_status")
            if pd.isna(status) or status not in ["active", "inactive", "closed"]:
                reasons.append("invalid_status")

            if reasons:
                row_dict = row.to_dict()
                row_dict["rejection_reasons"] = ";".join(reasons)
                rejected_rows.append(row_dict)
                for r in reasons:
                    rejection_counts[r] += 1
            else:
                valid_indices.append(idx)

        clean_df = df.loc[valid_indices].copy()
        clean_df["store_id"] = clean_df["store_id"].astype(str)
        clean_df["store_name"] = clean_df["store_name"].astype(str)
        clean_df["store_category"] = clean_df["store_category"].astype(str)
        clean_df["latitude"] = clean_df["latitude"].astype(float)
        clean_df["longitude"] = clean_df["longitude"].astype(float)
        clean_df["store_status"] = clean_df["store_status"].astype(str)

        clean_df = clean_df.sort_values(by="store_id").reset_index(drop=True)

        rejected_df = pd.DataFrame(rejected_rows)
        if len(rejected_df) == 0:
            rejected_df = pd.DataFrame(columns=list(df.columns) + ["rejection_reasons"])

        metrics = {
            "total_input_records": total_input,
            "valid_records": len(clean_df),
            "rejected_records": len(rejected_df),
            "rejection_rate_pct": round((len(rejected_df) / total_input) * 100, 2) if total_input else 0.0,
            "rejection_breakdown": rejection_counts,
        }

        return clean_df, rejected_df, metrics

    def save(
        self,
        clean_df: pd.DataFrame,
        rejected_df: pd.DataFrame,
        output_clean: Optional[Path] = None,
        output_rejected: Optional[Path] = None,
    ) -> Tuple[Path, Path]:
        clean_p = output_clean or (PATHS["data_processed"] / "cleaned_store_locations.csv")
        rej_p = output_rejected or (PATHS["data_rejected"] / "rejected_store_records.csv")

        clean_p.parent.mkdir(parents=True, exist_ok=True)
        rej_p.parent.mkdir(parents=True, exist_ok=True)

        clean_df.to_csv(clean_p, index=False)
        rejected_df.to_csv(rej_p, index=False)

        return clean_p, rej_p


def clean_store_locations_data(
    input_path: Optional[Path] = None,
    output_clean: Optional[Path] = None,
    output_rejected: Optional[Path] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    in_p = input_path or (PATHS["data_reference"] / "store_locations.csv")
    if not in_p.exists():
        raise FileNotFoundError(f"Store file not found at {in_p}. Run store generator first.")

    raw_df = pd.read_csv(in_p)
    cleaner = StoreDataCleaner()
    clean_df, rejected_df, metrics = cleaner.clean(raw_df)
    clean_p, rej_p = cleaner.save(clean_df, rejected_df, output_clean, output_rejected)

    print(f"[StoreDataCleaner] Cleaned {metrics['total_input_records']} -> {metrics['valid_records']} valid, "
          f"{metrics['rejected_records']} rejected")
    return clean_df, rejected_df, metrics


if __name__ == "__main__":
    clean_store_locations_data()
