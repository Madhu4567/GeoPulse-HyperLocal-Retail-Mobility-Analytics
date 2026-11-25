"""
GeoPulse Visit-to-Zone Mapping Engine
Associates confirmed retail store visits with commercial zones,
preserving strict visit grain (1 visit = 1 record) without double-counting.
"""
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import pandas as pd

import sys
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.settings import PATHS
from analytics.commercial_zoning.store_zone_mapping import map_stores_to_zones


class VisitZoneMapper:
    """Joins detected store visits with store-zone mapping to assign zone context to visit events."""

    def map_visits(
        self,
        visits_df: pd.DataFrame,
        store_zone_df: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Map visits to zones via store assignment."""
        if len(visits_df) == 0:
            raise ValueError("Input visits dataframe is empty.")
        if len(store_zone_df) == 0:
            raise ValueError("Input store-zone mapping is empty.")

        # Ensure no duplicate store_id rows in mapping
        store_map = store_zone_df.drop_duplicates(subset=["store_id"]).copy()

        # Left join visits with store zone mapping
        merged = visits_df.merge(
            store_map[[
                "store_id", "store_name", "store_category",
                "zone_id", "zone_name", "zone_type", "is_within_zone"
            ]],
            on="store_id",
            how="left",
        )

        # Handle unmapped stores gracefully
        merged["zone_id"] = merged["zone_id"].fillna("UNZONED")
        merged["zone_name"] = merged["zone_name"].fillna("Outside Commercial Zones")
        merged["zone_type"] = merged["zone_type"].fillna("Unassigned")
        merged["is_within_zone"] = merged["is_within_zone"].fillna(False)

        # Ensure strict 1-to-1 cardinality: len(merged) must equal len(visits_df)
        if len(merged) != len(visits_df):
            raise ValueError(f"Cardinality mismatch in visit-to-zone join: {len(merged)} vs {len(visits_df)}")

        # Ensure unique visit_id primary key
        if merged["visit_id"].nunique() != len(merged):
            raise ValueError("Duplicate visit_id found after zone mapping!")

        result_df = merged[[
            "visit_id",
            "user_id",
            "store_id",
            "store_name",
            "store_category",
            "zone_id",
            "zone_name",
            "zone_type",
            "arrival_time",
            "departure_time",
            "dwell_time_minutes",
            "observation_count",
            "min_distance_km",
            "visit_date",
            "is_within_zone",
        ]].copy()

        summary = {
            "total_visits_mapped": len(result_df),
            "unique_visitors": int(result_df["user_id"].nunique()),
            "visits_inside_commercial_zones": int(result_df["is_within_zone"].sum()),
            "visits_outside_commercial_zones": int((~result_df["is_within_zone"]).sum()),
            "zone_visit_distribution": result_df.groupby("zone_name")["visit_id"].count().to_dict(),
        }

        return result_df, summary

    def save(self, df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
        out_p = output_path or (PATHS["data_processed"] / "visit_zone_mapping.csv")
        out_p.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_p, index=False)
        return out_p


def map_visits_to_zones(
    visits_path: Optional[Path] = None,
    store_zone_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    v_path = visits_path or (PATHS["data_processed"] / "detected_store_visits.csv")
    sz_path = store_zone_path or (PATHS["data_processed"] / "store_zone_mapping.csv")

    if not v_path.exists():
        raise FileNotFoundError(f"Detected visits file not found at {v_path}.")

    if not sz_path.exists():
        map_stores_to_zones()

    visits_df = pd.read_csv(v_path)
    sz_df = pd.read_csv(sz_path)

    mapper = VisitZoneMapper()
    mapped_df, summary = mapper.map_visits(visits_df, sz_df)
    saved_p = mapper.save(mapped_df, output_path)

    print(f"[VisitZoneMapper] Mapped {summary['total_visits_mapped']} visits -> {summary['visits_inside_commercial_zones']} in commercial zones.")
    print(f"  Saved to: {saved_p}")
    return mapped_df, summary


if __name__ == "__main__":
    map_visits_to_zones()
