
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "processed"

FILES = {
    "footfall": DATA_DIR / "store_footfall.csv",
    "performance": DATA_DIR / "store_performance.csv",
    "catchment": DATA_DIR / "store_catchment_analysis.csv",
    "mobility": DATA_DIR / "store_mobility_insights.csv"
}

OUTPUT_FILE = DATA_DIR / "consolidated_store_insights.csv"


def main():

    print("Reading store analytics datasets...")

    for name, path in FILES.items():
        if not path.exists():
            raise FileNotFoundError(f"{name} file not found: {path}")

    footfall = pd.read_csv(FILES["footfall"])
    performance = pd.read_csv(FILES["performance"])
    performance = performance.drop(
    columns=["total_gps_pings", "unique_devices"],
    errors="ignore"
)
    catchment = pd.read_csv(FILES["catchment"])
    catchment = catchment.drop(
    columns=["total_gps_pings"],
    errors="ignore"
)
    mobility = pd.read_csv(FILES["mobility"])

    # Merge store-level analytics
    result = footfall.merge(
        performance,
        on=["nearest_store_id", "nearest_store_name"],
        how="left",
        suffixes=("", "_performance")
    )

    result = result.merge(
        catchment,
        on=["nearest_store_id", "nearest_store_name"],
        how="left",
        suffixes=("", "_catchment")
    )

    result = result.merge(
        mobility,
        on=["nearest_store_id", "nearest_store_name"],
        how="left",
        suffixes=("", "_mobility")
    )

    # Validate store-level uniqueness
    if result["nearest_store_id"].duplicated().any():
        raise ValueError("Duplicate stores found after merging!")

    # Sort by total GPS pings
    result = result.sort_values(
        by="total_gps_pings",
        ascending=False
    ).reset_index(drop=True)

    result.insert(0, "dashboard_rank", range(1, len(result) + 1))

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_FILE, index=False)

    print("\nConsolidated store insights generated!")
    print("Total stores:", len(result))
    print("Total columns:", len(result.columns))
    print("Output:", OUTPUT_FILE)

    print("\nDashboard-ready store summary:")
    print(result.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
