
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "data" / "processed" / "processed_gps_pings.csv"
OUTPUT_FILE = BASE_DIR / "data" / "processed" / "store_catchment_analysis.csv"


def generate_catchment_analysis():

    df = pd.read_csv(INPUT_FILE)

    print("Input GPS records:", len(df))

    # Distance bands
    bins = [0, 1, 3, 5, float("inf")]
    labels = ["0-1 km", "1-3 km", "3-5 km", "Above 5 km"]

    df["distance_band"] = pd.cut(
        df["distance_km"],
        bins=bins,
        labels=labels,
        right=True,
        include_lowest=True
    )

    # Store-level distance metrics
    catchment = (
        df.groupby(
            ["nearest_store_id", "nearest_store_name"],
            observed=True
        )
        .agg(
            total_gps_pings=("device_id", "count"),
            average_distance_km=("distance_km", "mean"),
            median_distance_km=("distance_km", "median"),
            minimum_distance_km=("distance_km", "min"),
            maximum_distance_km=("distance_km", "max")
        )
        .reset_index()
    )

    # Distance-band distribution
    band_summary = (
        df.groupby(
            ["nearest_store_id", "distance_band"],
            observed=False
        )
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )

    # Combine metrics
    catchment = catchment.merge(
        band_summary,
        on="nearest_store_id",
        how="left"
    )

    # Save output
    catchment = catchment.sort_values(
        "total_gps_pings",
        ascending=False
    )

    catchment.to_csv(OUTPUT_FILE, index=False)

    print("\nCatchment analysis completed")
    print("Total stores:", catchment["nearest_store_id"].nunique())
    print("Total GPS pings:", catchment["total_gps_pings"].sum())
    print("\nSample output:")
    print(catchment.head(5).to_string(index=False))
    print("\nOutput saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    generate_catchment_analysis()

