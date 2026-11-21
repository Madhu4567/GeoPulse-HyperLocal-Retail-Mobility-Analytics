
import pandas as pd
from pathlib import Path
from itertools import combinations
from math import radians, sin, cos, sqrt, atan2

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "data" / "raw" / "store_locations.csv"
OUTPUT_FILE = BASE_DIR / "data" / "processed" / "store_overlap_analysis.csv"


def haversine(lat1, lon1, lat2, lon2):
    earth_radius = 6371

    lat1, lon1, lat2, lon2 = map(
        radians, [lat1, lon1, lat2, lon2]
    )

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return earth_radius * c


def generate_store_overlap():

    stores = pd.read_csv(INPUT_FILE)

    print("Total stores:", len(stores))

    overlap_records = []

    # Generate unique store pairs
    for store_a, store_b in combinations(
        stores.to_dict("records"), 2
    ):

        distance = haversine(
            store_a["latitude"],
            store_a["longitude"],
            store_b["latitude"],
            store_b["longitude"]
        )

        overlap_records.append({
            "store_id_1": store_a["store_id"],
            "store_name_1": store_a["store_name"],
            "store_id_2": store_b["store_id"],
            "store_name_2": store_b["store_name"],
            "distance_km": round(distance, 3),
            "within_1_km": distance <= 1,
            "within_2_km": distance <= 2,
            "within_3_km": distance <= 3
        })

    overlap_df = pd.DataFrame(overlap_records)

    overlap_df = overlap_df.sort_values(
        "distance_km"
    ).reset_index(drop=True)

    overlap_df.to_csv(OUTPUT_FILE, index=False)

    print("\nStore overlap analysis completed")
    print("Total store pairs:", len(overlap_df))
    print("Pairs within 1 km:", overlap_df["within_1_km"].sum())
    print("Pairs within 2 km:", overlap_df["within_2_km"].sum())
    print("Pairs within 3 km:", overlap_df["within_3_km"].sum())

    print("\nClosest store pairs:")
    print(overlap_df.head(10).to_string(index=False))

    print("\nOutput saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    generate_store_overlap()
