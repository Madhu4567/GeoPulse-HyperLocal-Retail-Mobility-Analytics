"""
GeoPulse Store Visit Detection Engine
Extracts confirmed retail store visits from temporal clusters of proximity observations,
evaluating dwell time duration, observation density, and temporal gap thresholds.
"""
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import pandas as pd
import numpy as np

import sys
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.settings import SPATIAL_CONFIG, PATHS


class StoreVisitDetector:
    """Algorithmically filters proximity pings into verified store visits based on
    spatial proximity (<= 50m), dwell duration (>= 5 min), and temporal continuity.
    """

    def __init__(
        self,
        visit_radius_km: float = SPATIAL_CONFIG["store_visit_radius_km"],
        min_dwell_minutes: float = SPATIAL_CONFIG["min_dwell_time_minutes"],
        max_dwell_minutes: float = SPATIAL_CONFIG["max_dwell_time_minutes"],
        min_observations: int = SPATIAL_CONFIG["min_observations_per_visit"],
        max_gap_minutes: float = 30.0,
    ):
        self.visit_radius_km = visit_radius_km
        self.min_dwell_minutes = min_dwell_minutes
        self.max_dwell_minutes = max_dwell_minutes
        self.min_observations = min_observations
        self.max_gap_minutes = max_gap_minutes

    def detect_visits(self, mapped_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Identify store visits from nearest-store mapped GPS stream."""
        if len(mapped_df) == 0:
            raise ValueError("Mapped observations dataframe is empty.")

        # 1. Filter to candidate observations within visit radius
        candidates = mapped_df[mapped_df["distance_km"] <= self.visit_radius_km].copy()
        candidates["timestamp"] = pd.to_datetime(candidates["timestamp"], utc=True)
        candidates = candidates.sort_values(by=["user_id", "nearest_store_id", "timestamp"]).reset_index(drop=True)

        visits: List[Dict[str, Any]] = []
        visit_counter = 1

        # 2. Group by user and store to analyze dwell trajectories
        grouped = candidates.groupby(["user_id", "nearest_store_id"], sort=False)

        for (user_id, store_id), group in grouped:
            if len(group) < self.min_observations:
                continue

            timestamps = group["timestamp"].tolist()
            distances = group["distance_km"].tolist()

            # Cluster consecutive pings without excessive time gaps
            curr_cluster_times = [timestamps[0]]
            curr_cluster_dists = [distances[0]]

            for t, d in zip(timestamps[1:], distances[1:]):
                gap_minutes = (t - curr_cluster_times[-1]).total_seconds() / 60.0

                if gap_minutes <= self.max_gap_minutes:
                    curr_cluster_times.append(t)
                    curr_cluster_dists.append(d)
                else:
                    # Evaluate previous cluster
                    self._evaluate_cluster(
                        curr_cluster_times,
                        curr_cluster_dists,
                        user_id,
                        store_id,
                        visit_counter,
                        visits,
                    )
                    visit_counter = len(visits) + 1
                    curr_cluster_times = [t]
                    curr_cluster_dists = [d]

            # Evaluate final cluster in group
            if curr_cluster_times:
                self._evaluate_cluster(
                    curr_cluster_times,
                    curr_cluster_dists,
                    user_id,
                    store_id,
                    visit_counter,
                    visits,
                )
                visit_counter = len(visits) + 1

        visits_df = pd.DataFrame(visits)
        if len(visits_df) == 0:
            visits_df = pd.DataFrame(columns=[
                "visit_id", "user_id", "store_id", "arrival_time", "departure_time",
                "dwell_time_minutes", "observation_count", "min_distance_km", "visit_date"
            ])
        else:
            visits_df = visits_df.sort_values(by="arrival_time").reset_index(drop=True)

        metrics = {
            "total_candidate_pings_in_radius": len(candidates),
            "total_visits_detected": len(visits_df),
            "unique_visitors": int(visits_df["user_id"].nunique()) if len(visits_df) else 0,
            "unique_stores_visited": int(visits_df["store_id"].nunique()) if len(visits_df) else 0,
            "avg_dwell_time_minutes": float(np.round(visits_df["dwell_time_minutes"].mean(), 2)) if len(visits_df) else 0.0,
            "median_dwell_time_minutes": float(np.round(visits_df["dwell_time_minutes"].median(), 2)) if len(visits_df) else 0.0,
            "min_dwell_time_minutes": float(np.round(visits_df["dwell_time_minutes"].min(), 2)) if len(visits_df) else 0.0,
            "max_dwell_time_minutes": float(np.round(visits_df["dwell_time_minutes"].max(), 2)) if len(visits_df) else 0.0,
        }

        return visits_df, metrics

    def _evaluate_cluster(
        self,
        cluster_times: List[datetime],
        cluster_dists: List[float],
        user_id: str,
        store_id: str,
        visit_idx: int,
        visits_list: List[Dict[str, Any]],
    ) -> None:
        """Helper to qualify a cluster of pings against dwell and observation criteria."""
        obs_count = len(cluster_times)
        if obs_count < self.min_observations:
            return

        dwell_seconds = (cluster_times[-1] - cluster_times[0]).total_seconds()
        dwell_minutes = round(dwell_seconds / 60.0, 2)

        # Enforce dwell duration bounds
        if self.min_dwell_minutes <= dwell_minutes <= self.max_dwell_minutes:
            visits_list.append({
                "visit_id": f"VST_{len(visits_list) + 1:06d}",
                "user_id": user_id,
                "store_id": store_id,
                "arrival_time": cluster_times[0].strftime("%Y-%m-%dT%H:%M:%SZ"),
                "departure_time": cluster_times[-1].strftime("%Y-%m-%dT%H:%M:%SZ"),
                "dwell_time_minutes": dwell_minutes,
                "observation_count": obs_count,
                "min_distance_km": round(min(cluster_dists), 4),
                "visit_date": cluster_times[0].strftime("%Y-%m-%d"),
            })

    def save(self, df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
        out_p = output_path or (PATHS["data_processed"] / "detected_store_visits.csv")
        out_p.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_p, index=False)
        return out_p


def detect_store_visits(
    mapped_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    in_p = mapped_path or (PATHS["data_processed"] / "nearest_store_mapping.csv")
    if not in_p.exists():
        raise FileNotFoundError(f"Nearest store mapping not found at {in_p}. Run nearest store mapper first.")

    mapped_df = pd.read_csv(in_p)
    detector = StoreVisitDetector()
    visits_df, metrics = detector.detect_visits(mapped_df)
    saved_p = detector.save(visits_df, output_path)

    print(f"[StoreVisitDetector] Processed {metrics['total_candidate_pings_in_radius']} radius pings -> "
          f"Detected {metrics['total_visits_detected']} verified visits across {metrics['unique_visitors']} unique users.")
    print(f"  Average dwell time: {metrics['avg_dwell_time_minutes']} min | Median: {metrics['median_dwell_time_minutes']} min")
    print(f"  Saved to: {saved_p}")
    return visits_df, metrics


if __name__ == "__main__":
    detect_store_visits()
