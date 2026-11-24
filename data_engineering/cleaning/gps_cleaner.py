"""
GeoPulse GPS Mobility Data Cleaner
Validates, deduplicates, and sanitizes raw GPS mobility records,
routing non-conforming rows to rejected storage with diagnostic reasons.
"""
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import pandas as pd
import numpy as np

import sys
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.settings import DATA_CONFIG, PATHS


class GPSDataCleaner:
    """Modular cleaning pipeline for raw GPS observations."""

    def __init__(
        self,
        enforce_study_area: bool = True,
        max_accuracy_meters: float = 200.0,
    ):
        self.enforce_study_area = enforce_study_area
        self.max_accuracy_meters = max_accuracy_meters

    def clean(self, df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """Clean raw GPS records and return (valid_df, rejected_df, audit_metrics)."""
        df = df_raw.copy()
        total_input = len(df)

        rejected_rows: List[Dict[str, Any]] = []
        valid_indices: List[int] = []

        # Track audit reasons
        rejection_counts = {
            "missing_user_id": 0,
            "missing_timestamp": 0,
            "invalid_timestamp_format": 0,
            "future_timestamp": 0,
            "missing_latitude": 0,
            "missing_longitude": 0,
            "lat_out_of_wgs84": 0,
            "lon_out_of_wgs84": 0,
            "outside_study_area": 0,
            "invalid_accuracy": 0,
            "duplicate_observation": 0,
        }

        # Step 1: Missing User ID
        for idx, row in df.iterrows():
            reasons = []

            # Check User ID
            user_id = row.get("user_id")
            if pd.isna(user_id) or str(user_id).strip() == "":
                reasons.append("missing_user_id")

            # Check Timestamp
            ts_val = row.get("timestamp")
            if pd.isna(ts_val):
                reasons.append("missing_timestamp")
            else:
                try:
                    ts_dt = pd.to_datetime(ts_val, utc=True)
                    # Future check (beyond 2030)
                    if ts_dt.year > 2030:
                        reasons.append("future_timestamp")
                except Exception:
                    reasons.append("invalid_timestamp_format")

            # Check Latitude
            lat = row.get("latitude")
            if pd.isna(lat):
                reasons.append("missing_latitude")
            else:
                try:
                    lat_f = float(lat)
                    if lat_f < -90.0 or lat_f > 90.0:
                        reasons.append("lat_out_of_wgs84")
                    elif self.enforce_study_area:
                        if lat_f < (DATA_CONFIG["lat_min"] - 0.05) or lat_f > (DATA_CONFIG["lat_max"] + 0.05):
                            reasons.append("outside_study_area")
                except (ValueError, TypeError):
                    reasons.append("missing_latitude")

            # Check Longitude
            lon = row.get("longitude")
            if pd.isna(lon):
                reasons.append("missing_longitude")
            else:
                try:
                    lon_f = float(lon)
                    if lon_f < -180.0 or lon_f > 180.0:
                        reasons.append("lon_out_of_wgs84")
                    elif self.enforce_study_area:
                        if lon_f < (DATA_CONFIG["lon_min"] - 0.05) or lon_f > (DATA_CONFIG["lon_max"] + 0.05):
                            reasons.append("outside_study_area")
                except (ValueError, TypeError):
                    reasons.append("missing_longitude")

            # Check Accuracy
            acc = row.get("accuracy")
            if not pd.isna(acc):
                try:
                    acc_f = float(acc)
                    if acc_f <= 0.0 or acc_f > self.max_accuracy_meters:
                        reasons.append("invalid_accuracy")
                except (ValueError, TypeError):
                    reasons.append("invalid_accuracy")

            if reasons:
                row_dict = row.to_dict()
                row_dict["rejection_reasons"] = ";".join(reasons)
                rejected_rows.append(row_dict)
                for r in reasons:
                    rejection_counts[r] += 1
            else:
                valid_indices.append(idx)

        # Build candidate valid dataframe
        valid_df = df.loc[valid_indices].copy()

        # Step 2: Deduplication on (user_id, timestamp)
        # Find duplicates within valid candidates
        is_dupe = valid_df.duplicated(subset=["user_id", "timestamp"], keep="first")
        dupe_df = valid_df[is_dupe].copy()
        for _, row in dupe_df.iterrows():
            row_dict = row.to_dict()
            row_dict["rejection_reasons"] = "duplicate_observation"
            rejected_rows.append(row_dict)
            rejection_counts["duplicate_observation"] += 1

        clean_df = valid_df[~is_dupe].copy()

        # Standardize data types
        clean_df["user_id"] = clean_df["user_id"].astype(str)
        clean_df["timestamp"] = pd.to_datetime(clean_df["timestamp"], utc=True)
        clean_df["latitude"] = clean_df["latitude"].astype(float)
        clean_df["longitude"] = clean_df["longitude"].astype(float)
        clean_df["accuracy"] = clean_df["accuracy"].astype(float)
        if "location_id" in clean_df.columns:
            clean_df["location_id"] = clean_df["location_id"].astype(str)

        clean_df = clean_df.sort_values(by=["user_id", "timestamp"]).reset_index(drop=True)

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
        """Save cleaned and rejected datasets."""
        clean_p = output_clean or (PATHS["data_processed"] / "cleaned_gps_mobility.csv")
        rej_p = output_rejected or (PATHS["data_rejected"] / "rejected_gps_records.csv")

        clean_p.parent.mkdir(parents=True, exist_ok=True)
        rej_p.parent.mkdir(parents=True, exist_ok=True)

        clean_df.to_csv(clean_p, index=False)
        rejected_df.to_csv(rej_p, index=False)

        return clean_p, rej_p


def clean_gps_mobility_data(
    input_path: Optional[Path] = None,
    output_clean: Optional[Path] = None,
    output_rejected: Optional[Path] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """Clean GPS raw data and persist outputs."""
    in_p = input_path or (PATHS["data_raw"] / "gps_mobility.csv")
    if not in_p.exists():
        raise FileNotFoundError(f"Raw GPS file not found at {in_p}. Run generator first.")

    raw_df = pd.read_csv(in_p)
    cleaner = GPSDataCleaner()
    clean_df, rejected_df, metrics = cleaner.clean(raw_df)
    clean_p, rej_p = cleaner.save(clean_df, rejected_df, output_clean, output_rejected)

    print(f"[GPSDataCleaner] Cleaned {metrics['total_input_records']} -> {metrics['valid_records']} valid, "
          f"{metrics['rejected_records']} rejected ({metrics['rejection_rate_pct']}%)")
    return clean_df, rejected_df, metrics


if __name__ == "__main__":
    clean_gps_mobility_data()
