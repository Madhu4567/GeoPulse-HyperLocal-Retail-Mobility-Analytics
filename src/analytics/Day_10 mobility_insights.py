
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "processed_gps_pings.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "store_mobility_insights.csv"
)


def main():

    print("Reading processed GPS data...")

    df = pd.read_csv(INPUT_FILE)

    required_columns = {
        "device_id",
        "nearest_store_id",
        "nearest_store_name"
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(f"Missing columns: {missing}")

    # Store-wise unique device count
    store_summary = (
        df.groupby(
            ["nearest_store_id", "nearest_store_name"]
        )["device_id"]
        .nunique()
        .reset_index(name="unique_devices")
    )

    # Number of distinct stores associated with each device
    device_summary = (
        df.groupby("device_id")["nearest_store_id"]
        .nunique()
        .reset_index(name="stores_observed")
    )

    # Devices observed across multiple stores
    multi_store_devices = device_summary[
        device_summary["stores_observed"] > 1
    ]

    # Count multi-store devices associated with each store
    multi_store_counts = (
        df[df["device_id"].isin(multi_store_devices["device_id"])]
        .groupby("nearest_store_id")["device_id"]
        .nunique()
        .reset_index(name="multi_store_devices")
    )

    # Combine store-level metrics
    result = store_summary.merge(
        multi_store_counts,
        on="nearest_store_id",
        how="left"
    )

    result["multi_store_devices"] = (
        result["multi_store_devices"].fillna(0).astype(int)
    )

    result["mobility_percentage"] = (
        result["multi_store_devices"]
        / result["unique_devices"] * 100
    ).round(2)

    result = result.sort_values(
        by="multi_store_devices",
        ascending=False
    ).reset_index(drop=True)

    result.insert(0, "mobility_rank", range(1, len(result) + 1))

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_FILE, index=False)

    print("\nStore mobility insights completed!")
    print("Total stores:", len(result))
    print("Total devices:", df["device_id"].nunique())
    print("Devices observed across multiple stores:", len(multi_store_devices))
    print("Output:", OUTPUT_FILE)

    print("\nStore mobility summary:")
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()

