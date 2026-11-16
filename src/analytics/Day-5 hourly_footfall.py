
import pandas as pd
from pathlib import Path

# Define input and output paths
BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "data" / "processed" / "processed_gps_pings.csv"
OUTPUT_FILE = BASE_DIR / "data" / "processed" / "hourly_footfall.csv"


def generate_hourly_footfall():

    # Read processed GPS data
    df = pd.read_csv(INPUT_FILE)

    print(f"Input records: {len(df)}")

    # Convert timestamp column to datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # Remove records with invalid timestamps or missing store details
    df = df.dropna(
        subset=["timestamp", "nearest_store_id", "nearest_store_name"]
    ).copy()

    # Extract hour from timestamp
    df["hour"] = df["timestamp"].dt.hour

    # Aggregate GPS pings by store and hour
    hourly_data = (
        df.groupby(
            ["nearest_store_id", "nearest_store_name", "hour"]
        )
        .size()
        .reset_index(name="total_gps_pings")
    )

    # Sort results
    hourly_data = hourly_data.sort_values(
        ["nearest_store_id", "hour"]
    )

    # Save output
    hourly_data.to_csv(OUTPUT_FILE, index=False)

    print(f"Output records: {len(hourly_data)}")
    print(f"Total GPS pings aggregated: {hourly_data['total_gps_pings'].sum()}")
    print(f"Output saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    generate_hourly_footfall()
