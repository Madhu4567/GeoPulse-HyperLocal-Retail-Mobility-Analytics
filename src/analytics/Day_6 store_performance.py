
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

STORE_FILE = BASE_DIR / "data" / "processed" / "store_footfall.csv"
HOURLY_FILE = BASE_DIR / "data" / "processed" / "hourly_footfall.csv"
OUTPUT_FILE = BASE_DIR / "data" / "processed" / "store_performance.csv"


def generate_store_performance():

    # Read input datasets
    store_df = pd.read_csv(STORE_FILE)
    hourly_df = pd.read_csv(HOURLY_FILE)

    # Identify peak activity hour for each store
    peak_hour = (
        hourly_df.sort_values(
            ["nearest_store_id", "total_gps_pings", "hour"],
            ascending=[True, False, True]
        )
        .drop_duplicates(subset=["nearest_store_id"])
        [["nearest_store_id", "hour", "total_gps_pings"]]
        .rename(columns={
            "hour": "peak_hour",
            "total_gps_pings": "peak_hour_gps_pings"
        })
    )

    # Combine store-level and hourly analytics
    performance_df = store_df.merge(
        peak_hour,
        on="nearest_store_id",
        how="left"
    )

    # Rank stores based on total GPS pings
    performance_df = performance_df.sort_values(
        "total_gps_pings",
        ascending=False
    ).reset_index(drop=True)

    performance_df["store_rank"] = range(1, len(performance_df) + 1)

    # Save output
    performance_df.to_csv(OUTPUT_FILE, index=False)

    print("Store Performance Analysis Completed")
    print("Total stores:", len(performance_df))
    print("Total GPS pings:", performance_df["total_gps_pings"].sum())
    print("\nTop 5 stores:")
    print(performance_df.head(5).to_string(index=False))

    print("\nBottom 5 stores:")
    print(performance_df.tail(5).to_string(index=False))

    print("\nOutput saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    generate_store_performance()
