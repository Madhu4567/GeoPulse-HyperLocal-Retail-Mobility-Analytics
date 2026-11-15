
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "data" / "processed" / "processed_gps_pings.csv"
OUTPUT_FILE = BASE_DIR / "data" / "processed" / "store_footfall.csv"


def main():
    print("Reading processed GPS data...")

    df = pd.read_csv(INPUT_FILE)

    required_columns = [
        "nearest_store_id",
        "nearest_store_name",
        "device_id"
    ]

    missing_columns = [
        col for col in required_columns if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(f"Missing columns: {missing_columns}")

    print("Calculating store-level footfall...")

    footfall_df = (
        df.groupby(
            ["nearest_store_id", "nearest_store_name"]
        )
        .agg(
            total_gps_pings=("device_id", "count"),
            unique_devices=("device_id", "nunique")
        )
        .reset_index()
    )

    footfall_df = footfall_df.sort_values(
        "total_gps_pings",
        ascending=False
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    footfall_df.to_csv(OUTPUT_FILE, index=False)

    # Validations
    assert len(df) == 5000
    assert footfall_df["nearest_store_id"].notna().all()
    assert footfall_df["total_gps_pings"].sum() == len(df)

    print("\nStore-level footfall completed!")
    print(footfall_df.to_string(index=False))
    print("\nTotal GPS records:", len(df))
    print("Total stores:", len(footfall_df))
    print("Output saved:", OUTPUT_FILE)
    print("All validations passed!")


if __name__ == "__main__":
    main()
