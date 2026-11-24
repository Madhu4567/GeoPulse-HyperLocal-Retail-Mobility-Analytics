"""
GeoPulse Synthetic GPS Mobility Data Generator
Simulates realistic urban mobility patterns, store visits, transit corridors,
and controlled data anomalies for quality pipeline testing.
"""
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import random
import json
import pandas as pd
import numpy as np

import sys
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.settings import DATA_CONFIG, PATHS
from data_engineering.generation.store_generator import generate_synthetic_stores


class GPSDataGenerator:
    """Generates synthetic GPS mobility stream with realistic movement corridors,
    retail dwell clusters, and controlled noise/anomalies for quality checks.
    """

    def __init__(
        self,
        num_users: int = DATA_CONFIG["default_num_users"],
        target_pings: int = DATA_CONFIG["default_num_pings"],
        stores_df: Optional[pd.DataFrame] = None,
        random_seed: int = DATA_CONFIG["random_seed"],
        anomaly_rate: float = 0.02,  # 2% deliberate anomalies for DQ testing
    ):
        self.num_users = num_users
        self.target_pings = target_pings
        self.random_seed = random_seed
        self.anomaly_rate = anomaly_rate

        random.seed(self.random_seed)
        np.random.seed(self.random_seed)

        # Load or generate store locations for anchor proximity
        if stores_df is not None:
            self.stores = stores_df[stores_df["store_status"] == "active"].copy()
        else:
            stores_path = PATHS["data_reference"] / "store_locations.csv"
            if stores_path.exists():
                raw_stores = pd.read_csv(stores_path)
                self.stores = raw_stores[raw_stores["store_status"] == "active"].copy()
            else:
                self.stores = generate_synthetic_stores(random_seed=self.random_seed)
                self.stores = self.stores[self.stores["store_status"] == "active"].copy()

        self.start_dt = datetime.fromisoformat(DATA_CONFIG["date_start"].replace("Z", "+00:00"))
        self.end_dt = datetime.fromisoformat(DATA_CONFIG["date_end"].replace("Z", "+00:00"))
        self.total_seconds = int((self.end_dt - self.start_dt).total_seconds())

    def _generate_user_pings(self, user_id: str, ping_count: int) -> List[Dict[str, Any]]:
        """Generate a realistic sequence of pings for a single user."""
        user_pings: List[Dict[str, Any]] = []

        # Assign user a home anchor and a work anchor in the study area
        home_lat = np.random.uniform(DATA_CONFIG["lat_min"] + 0.01, DATA_CONFIG["lat_max"] - 0.01)
        home_lon = np.random.uniform(DATA_CONFIG["lon_min"] + 0.01, DATA_CONFIG["lon_max"] - 0.01)

        # Pick random day and start time within study window
        day_offset = random.randint(0, 6)
        curr_time = self.start_dt + timedelta(
            days=day_offset,
            hours=random.randint(8, 12),
            minutes=random.randint(0, 59),
        )

        curr_lat = home_lat
        curr_lon = home_lon

        # User trajectory state: walking, transit, or visiting store
        pings_remaining = ping_count
        while pings_remaining > 0:
            activity = random.choices(["transit", "store_visit", "stationary"], weights=[0.45, 0.35, 0.20], k=1)[0]

            if activity == "store_visit" and len(self.stores) > 0 and pings_remaining >= 3:
                # Pick a store to visit
                target_store = self.stores.sample(1, random_state=random.randint(1, 10000)).iloc[0]
                store_lat = target_store["latitude"]
                store_lon = target_store["longitude"]

                # Dwell observations: 3 to 7 consecutive pings inside 15-40m of store
                dwell_pings = min(random.randint(3, 7), pings_remaining)
                for _ in range(dwell_pings):
                    # 0.0001 deg is ~11 meters
                    lat_noise = np.random.normal(0, 0.00015)
                    lon_noise = np.random.normal(0, 0.00015)
                    ping_lat = round(store_lat + lat_noise, 6)
                    ping_lon = round(store_lon + lon_noise, 6)
                    accuracy = round(float(np.random.uniform(3.0, 15.0)), 1)

                    user_pings.append({
                        "user_id": user_id,
                        "timestamp": curr_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "latitude": ping_lat,
                        "longitude": ping_lon,
                        "accuracy": accuracy,
                        "location_id": f"LOC_{random.randint(100000, 999999)}",
                    })
                    curr_time += timedelta(minutes=random.randint(2, 8), seconds=random.randint(0, 59))

                pings_remaining -= dwell_pings
                curr_lat = store_lat
                curr_lon = store_lon

            elif activity == "transit":
                # User moving along corridor towards a destination
                step_lat = np.random.normal(0, 0.002)
                step_lon = np.random.normal(0, 0.002)
                curr_lat = max(DATA_CONFIG["lat_min"], min(DATA_CONFIG["lat_max"], curr_lat + step_lat))
                curr_lon = max(DATA_CONFIG["lon_min"], min(DATA_CONFIG["lon_max"], curr_lon + step_lon))

                accuracy = round(float(np.random.uniform(8.0, 35.0)), 1)
                user_pings.append({
                    "user_id": user_id,
                    "timestamp": curr_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "latitude": round(curr_lat, 6),
                    "longitude": round(curr_lon, 6),
                    "accuracy": accuracy,
                    "location_id": f"LOC_{random.randint(100000, 999999)}",
                })
                curr_time += timedelta(minutes=random.randint(5, 25), seconds=random.randint(0, 59))
                pings_remaining -= 1

            else:  # stationary
                curr_time += timedelta(minutes=random.randint(15, 60))
                accuracy = round(float(np.random.uniform(4.0, 18.0)), 1)
                user_pings.append({
                    "user_id": user_id,
                    "timestamp": curr_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "latitude": round(curr_lat + np.random.normal(0, 0.0001), 6),
                    "longitude": round(curr_lon + np.random.normal(0, 0.0001), 6),
                    "accuracy": accuracy,
                    "location_id": f"LOC_{random.randint(100000, 999999)}",
                })
                pings_remaining -= 1

        return user_pings

    def generate(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Generate entire GPS dataset including controlled injection of anomalies."""
        all_pings: List[Dict[str, Any]] = []
        pings_per_user = max(5, self.target_pings // self.num_users)

        for i in range(1, self.num_users + 1):
            user_id = f"USR_{i:04d}"
            # Vary pings per user between 50% and 150% of average
            user_target = int(pings_per_user * np.random.uniform(0.6, 1.4))
            pings = self._generate_user_pings(user_id, max(4, user_target))
            all_pings.extend(pings)

        df = pd.DataFrame(all_pings)

        # Inject controlled anomalies for data quality validation testing
        anomaly_count = int(len(df) * self.anomaly_rate)
        injected_anomalies = {
            "out_of_bounds_lat": 0,
            "out_of_bounds_lon": 0,
            "missing_lat": 0,
            "missing_lon": 0,
            "missing_user_id": 0,
            "duplicate_records": 0,
            "invalid_accuracy": 0,
        }

        if anomaly_count > 0 and len(df) > 50:
            indices = np.random.choice(df.index, size=anomaly_count, replace=False)
            sub_splits = np.array_split(indices, 7)

            # 1. Out of bounds latitude (> 90)
            for idx in sub_splits[0]:
                df.at[idx, "latitude"] = 94.250000
                injected_anomalies["out_of_bounds_lat"] += 1

            # 2. Out of bounds longitude (< -180)
            for idx in sub_splits[1]:
                df.at[idx, "longitude"] = -195.120000
                injected_anomalies["out_of_bounds_lon"] += 1

            # 3. Missing latitude
            for idx in sub_splits[2]:
                df.at[idx, "latitude"] = np.nan
                injected_anomalies["missing_lat"] += 1

            # 4. Missing longitude
            for idx in sub_splits[3]:
                df.at[idx, "longitude"] = np.nan
                injected_anomalies["missing_lon"] += 1

            # 5. Missing user_id
            for idx in sub_splits[4]:
                df.at[idx, "user_id"] = None
                injected_anomalies["missing_user_id"] += 1

            # 6. Invalid accuracy (< 0)
            for idx in sub_splits[5]:
                df.at[idx, "accuracy"] = -15.0
                injected_anomalies["invalid_accuracy"] += 1

            # 7. Exact duplicates (append duplicate rows)
            dupe_rows = df.loc[sub_splits[6]].copy()
            df = pd.concat([df, dupe_rows], ignore_index=True)
            injected_anomalies["duplicate_records"] = len(dupe_rows)

        # Compute generation summary
        valid_coords = df.dropna(subset=["latitude", "longitude"])
        valid_bounded = valid_coords[
            (valid_coords["latitude"].between(-90, 90)) &
            (valid_coords["longitude"].between(-180, 180))
        ]

        summary = {
            "total_observations": len(df),
            "unique_users": int(df["user_id"].nunique(dropna=True)),
            "date_range_start": str(df["timestamp"].dropna().min()),
            "date_range_end": str(df["timestamp"].dropna().max()),
            "geographic_bounds": {
                "min_lat": float(valid_bounded["latitude"].min()) if len(valid_bounded) else None,
                "max_lat": float(valid_bounded["latitude"].max()) if len(valid_bounded) else None,
                "min_lon": float(valid_bounded["longitude"].min()) if len(valid_bounded) else None,
                "max_lon": float(valid_bounded["longitude"].max()) if len(valid_bounded) else None,
            },
            "injected_anomalies": injected_anomalies,
            "total_anomalies": sum(injected_anomalies.values()),
        }

        return df, summary

    def save(
        self,
        df: pd.DataFrame,
        summary: Dict[str, Any],
        output_csv: Optional[Path] = None,
        summary_json: Optional[Path] = None,
    ) -> Tuple[Path, Path]:
        """Persist generated dataframe and summary metadata."""
        csv_path = output_csv or (PATHS["data_raw"] / "gps_mobility.csv")
        summary_path = summary_json or (PATHS["data_raw"] / "gps_generation_summary.json")

        csv_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(csv_path, index=False)

        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        return csv_path, summary_path


def generate_synthetic_gps_data(
    num_users: int = DATA_CONFIG["default_num_users"],
    target_pings: int = DATA_CONFIG["default_num_pings"],
    output_path: Optional[Path] = None,
    random_seed: int = DATA_CONFIG["random_seed"],
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Helper function to execute GPS generation and persistence."""
    generator = GPSDataGenerator(
        num_users=num_users,
        target_pings=target_pings,
        random_seed=random_seed,
    )
    df, summary = generator.generate()
    csv_p, sum_p = generator.save(df, summary, output_csv=output_path)
    print(f"[GPSDataGenerator] Generated {len(df)} pings across {summary['unique_users']} users.")
    print(f"[GPSDataGenerator] Saved to {csv_p} (Summary: {sum_p})")
    return df, summary


if __name__ == "__main__":
    generate_synthetic_gps_data()
