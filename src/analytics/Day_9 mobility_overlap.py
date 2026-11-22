
from pathlib import Path
from itertools import combinations

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "data" / "processed" / "processed_gps_pings.csv"
OUTPUT_FILE = BASE_DIR / "data" / "processed" / "mobility_overlap_analysis.csv"


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
        raise ValueError(f"Missing required columns: {missing}")

    # Get unique devices assigned to each store
    store_devices = (
        df.groupby(["nearest_store_id", "nearest_store_name"])["device_id"]
        .apply(lambda x: set(x.unique()))
        .to_dict()
    )

    results = []

    # Generate all possible store pairs
    for (store1_id, store1_name), (store2_id, store2_name) in combinations(
        store_devices.keys(), 2
    ):

        devices1 = store_devices[(store1_id, store1_name)]
        devices2 = store_devices[(store2_id, store2_name)]

        shared_devices = devices1.intersection(devices2)
        union_devices = devices1.union(devices2)

        shared_count = len(shared_devices)

        jaccard_overlap = (
            shared_count / len(union_devices) * 100
            if union_devices else 0
        )

        results.append({
            "store1_id": store1_id,
            "store1_name": store1_name,
            "store2_id": store2_id,
            "store2_name": store2_name,
            "store1_unique_devices": len(devices1),
            "store2_unique_devices": len(devices2),
            "shared_devices": shared_count,
            "jaccard_overlap_percentage": round(jaccard_overlap, 2)
        })

    result_df = pd.DataFrame(results)

    result_df = result_df.sort_values(
        by=["jaccard_overlap_percentage", "shared_devices"],
        ascending=False
    )

    result_df.insert(
        0,
        "overlap_rank",
        range(1, len(result_df) + 1)
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(OUTPUT_FILE, index=False)

    print("\nMobility overlap analysis completed!")
    print(f"Total store pairs: {len(result_df)}")
    print(f"Output saved to: {OUTPUT_FILE}")

    print("\nTop 10 store pairs:")
    print(result_df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
