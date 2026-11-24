"""
GeoPulse Nearest Store Mapping Engine
Associates cleaned GPS mobility observations with their geographically closest retail store
using vectorized great-circle distance matrix evaluation.
"""
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import pandas as pd
import numpy as np

import sys
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.settings import SPATIAL_CONFIG, PATHS
from data_engineering.spatial.haversine import haversine_vectorized


class NearestStoreMapper:
    """Performs vectorized nearest-store association on GPS observations."""

    def __init__(
        self,
        max_threshold_km: float = SPATIAL_CONFIG["nearest_store_max_distance_km"],
        only_active_stores: bool = True,
    ):
        self.max_threshold_km = max_threshold_km
        self.only_active_stores = only_active_stores

    def map_nearest(
        self,
        gps_df: pd.DataFrame,
        stores_df: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Map every GPS observation to its nearest retail store."""
        if len(gps_df) == 0:
            raise ValueError("Input GPS dataframe is empty.")
        if len(stores_df) == 0:
            raise ValueError("Input stores dataframe is empty.")

        stores = stores_df.copy()
        if self.only_active_stores and "store_status" in stores.columns:
            stores = stores[stores["store_status"] == "active"].copy()

        if len(stores) == 0:
            raise ValueError("No eligible active stores available for mapping.")

        # Ensure consistent order for deterministic tie-breaking
        stores = stores.sort_values(by="store_id").reset_index(drop=True)

        p_lats = gps_df["latitude"].to_numpy(dtype=np.float64)[:, np.newaxis]   # (N, 1)
        p_lons = gps_df["longitude"].to_numpy(dtype=np.float64)[:, np.newaxis]  # (N, 1)

        s_lats = stores["latitude"].to_numpy(dtype=np.float64)[np.newaxis, :]   # (1, M)
        s_lons = stores["longitude"].to_numpy(dtype=np.float64)[np.newaxis, :]  # (1, M)

        # Compute (N, M) distance matrix via broadcasted haversine
        dist_matrix = haversine_vectorized(p_lats, p_lons, s_lats, s_lons)  # (N, M)

        # Nearest store index and distance for each point
        nearest_indices = np.argmin(dist_matrix, axis=1)
        min_distances = np.take_along_axis(dist_matrix, nearest_indices[:, np.newaxis], axis=1).squeeze(axis=1)

        result_df = gps_df.copy()
        result_df["nearest_store_id"] = stores.iloc[nearest_indices]["store_id"].values
        result_df["distance_km"] = np.round(min_distances, 4)
        result_df["within_distance_threshold"] = result_df["distance_km"] <= self.max_threshold_km

        # Add optional store category / name context for downstream analytics
        store_cat_map = dict(zip(stores["store_id"], stores["store_category"]))
        store_name_map = dict(zip(stores["store_id"], stores["store_name"]))
        result_df["store_name"] = result_df["nearest_store_id"].map(store_name_map)
        result_df["store_category"] = result_df["nearest_store_id"].map(store_cat_map)

        metrics = {
            "total_mapped_points": len(result_df),
            "points_within_threshold": int(result_df["within_distance_threshold"].sum()),
            "points_beyond_threshold": int((~result_df["within_distance_threshold"]).sum()),
            "avg_distance_to_nearest_store_km": float(np.round(result_df["distance_km"].mean(), 3)),
            "median_distance_to_nearest_store_km": float(np.round(result_df["distance_km"].median(), 3)),
            "min_distance_km": float(np.round(result_df["distance_km"].min(), 4)),
            "max_distance_km": float(np.round(result_df["distance_km"].max(), 3)),
            "unique_nearest_stores_matched": int(result_df["nearest_store_id"].nunique()),
        }

        return result_df, metrics

    def save(self, df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
        out_p = output_path or (PATHS["data_processed"] / "nearest_store_mapping.csv")
        out_p.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_p, index=False)
        return out_p


def map_nearest_stores(
    gps_path: Optional[Path] = None,
    stores_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    gps_p = gps_path or (PATHS["data_processed"] / "cleaned_gps_mobility.csv")
    stores_p = stores_path or (PATHS["data_processed"] / "cleaned_store_locations.csv")

    if not gps_p.exists():
        raise FileNotFoundError(f"Cleaned GPS dataset not found at {gps_p}.")
    if not stores_p.exists():
        stores_p = PATHS["data_reference"] / "store_locations.csv"
        if not stores_p.exists():
            raise FileNotFoundError(f"Store locations dataset not found at {stores_p}.")

    gps_df = pd.read_csv(gps_p)
    stores_df = pd.read_csv(stores_p)

    mapper = NearestStoreMapper()
    mapped_df, metrics = mapper.map_nearest(gps_df, stores_df)
    saved_p = mapper.save(mapped_df, output_path)

    print(f"[NearestStoreMapper] Successfully mapped {metrics['total_mapped_points']} observations.")
    print(f"  Within threshold ({SPATIAL_CONFIG['nearest_store_max_distance_km']} km): {metrics['points_within_threshold']}")
    print(f"  Average distance: {metrics['avg_distance_to_nearest_store_km']} km | Median: {metrics['median_distance_to_nearest_store_km']} km")
    print(f"  Saved to: {saved_p}")
    return mapped_df, metrics


if __name__ == "__main__":
    map_nearest_stores()
