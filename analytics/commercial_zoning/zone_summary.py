"""
GeoPulse Commercial Zone Summarizer
Compiles zone-level retail performance summaries including store counts,
total footfall, unique visitor volume, dwell times, top categories, and daily averages.
"""
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import pandas as pd
import numpy as np

import sys
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.settings import PATHS
from analytics.commercial_zoning.visit_zone_mapping import map_visits_to_zones


class CommercialZoneSummarizer:
    """Summarizes footfall and retail vitality across commercial zones."""

    def summarize(
        self,
        visit_zone_df: pd.DataFrame,
        store_zone_df: pd.DataFrame,
        zones_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Compile zone summary metrics."""
        # Zone store counts
        store_counts = store_zone_df[store_zone_df["zone_id"] != "UNZONED"].groupby("zone_id")["store_id"].nunique().to_dict()

        # Filter visits inside valid zones
        zone_visits = visit_zone_df[visit_zone_df["zone_id"] != "UNZONED"].copy()

        summary_rows = []

        for _, zone in zones_df.iterrows():
            zid = zone["zone_id"]
            zname = zone["zone_name"]
            ztype = zone["zone_type"]
            area_sq_km = float(zone["area_sq_km"])

            z_sub = zone_visits[zone_visits["zone_id"] == zid]
            total_visits = len(z_sub)
            unique_visitors = int(z_sub["user_id"].nunique()) if total_visits > 0 else 0
            avg_dwell = round(float(z_sub["dwell_time_minutes"].mean()), 2) if total_visits > 0 else 0.0

            # Distinct days active in dataset
            distinct_days = max(1, z_sub["visit_date"].nunique()) if total_visits > 0 else 1
            daily_avg_footfall = round(total_visits / distinct_days, 2)

            # Most popular category in zone
            if total_visits > 0:
                cat_counts = z_sub["store_category"].value_counts()
                top_category = cat_counts.index[0] if len(cat_counts) > 0 else "N/A"
            else:
                top_category = "N/A"

            store_count = store_counts.get(zid, 0)
            density_score = round(total_visits / area_sq_km, 2) if area_sq_km > 0 else 0.0

            summary_rows.append({
                "zone_id": zid,
                "zone_name": zname,
                "zone_type": ztype,
                "area_sq_km": area_sq_km,
                "store_count": store_count,
                "total_visits": total_visits,
                "unique_visitors": unique_visitors,
                "avg_dwell_time_minutes": avg_dwell,
                "most_popular_category": top_category,
                "daily_avg_footfall": daily_avg_footfall,
                "visits_per_sq_km": density_score,
            })

        summary_df = pd.DataFrame(summary_rows)
        summary_df = summary_df.sort_values(by="total_visits", ascending=False).reset_index(drop=True)
        return summary_df

    def save(self, df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
        out_p = output_path or (PATHS["data_processed"] / "commercial_zone_summary.csv")
        out_p.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_p, index=False)
        return out_p


def summarize_commercial_zones(
    visit_zone_path: Optional[Path] = None,
    store_zone_path: Optional[Path] = None,
    zones_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
) -> pd.DataFrame:
    vz_p = visit_zone_path or (PATHS["data_processed"] / "visit_zone_mapping.csv")
    sz_p = store_zone_path or (PATHS["data_processed"] / "store_zone_mapping.csv")
    z_p = zones_path or (PATHS["data_reference"] / "commercial_zones.csv")

    if not vz_p.exists() or not sz_p.exists():
        map_visits_to_zones()

    vz_df = pd.read_csv(vz_p)
    sz_df = pd.read_csv(sz_p)
    z_df = pd.read_csv(z_p)

    summarizer = CommercialZoneSummarizer()
    summary_df = summarizer.summarize(vz_df, sz_df, z_df)
    saved_p = summarizer.save(summary_df, output_path)

    print(f"[CommercialZoneSummarizer] Summarized {len(summary_df)} commercial zones.")
    print(f"  Top Zone by Footfall: {summary_df.iloc[0]['zone_name']} ({summary_df.iloc[0]['total_visits']} visits)")
    print(f"  Saved to: {saved_p}")
    return summary_df


if __name__ == "__main__":
    summarize_commercial_zones()
