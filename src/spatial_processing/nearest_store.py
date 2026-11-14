
from pathlib import Path
import pandas as pd
import numpy as np

# Project paths
BASE_DIR = Path(__file__).resolve().parents[2]

GPS_FILE = BASE_DIR / "data" / "raw" / "gps_pings.csv"
STORE_FILE = BASE_DIR / "data" / "raw" / "store_locations.csv"
OUTPUT_DIR = BASE_DIR / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Read input datasets
gps_df = pd.read_csv(GPS_FILE)
stores_df = pd.read_csv(STORE_FILE)

# Haversine distance calculation in kilometers

def haversine(lat1, lon1, lat2, lon2):
    earth_radius = 6371

    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat1) * np.cos(lat2)
        * np.sin(dlon / 2) ** 2
    )

    return 2 * earth_radius * np.arcsin(
        np.sqrt(a)
    )


# Find nearest store for every GPS ping
nearest_stores = []

for _, ping in gps_df.iterrows():

    distances = haversine(
        ping["latitude"],
        ping["longitude"],
        stores_df["latitude"].to_numpy(),
        stores_df["longitude"].to_numpy()
    )

    nearest_index = np.argmin(distances)
    nearest_store = stores_df.iloc[nearest_index]

    nearest_stores.append({
        "device_id": ping["device_id"],
        "timestamp": ping["timestamp"],
        "latitude": ping["latitude"],
        "longitude": ping["longitude"],
        "nearest_store_id": nearest_store["store_id"],
        "nearest_store_name": nearest_store["store_name"],
        "distance_km": distances[nearest_index]
    })


# Save processed output
result_df = pd.DataFrame(nearest_stores)

output_file = OUTPUT_DIR / "processed_gps_pings.csv"
result_df.to_csv(output_file, index=False)

print("Nearest store mapping completed!")
print("Total GPS records:", len(result_df))
print("Unique devices:", result_df["device_id"].nunique())
print("Output saved:", output_file)
print(result_df.head())


# Validate nearest store output

assert len(result_df) == 5000
assert result_df["nearest_store_id"].notna().all()
assert result_df["distance_km"].notna().all()
assert (result_df["distance_km"] >= 0).all()

print("Record count validation: PASSED")
print("Nearest store validation: PASSED")
print("Distance validation: PASSED")

print("\nNearest store distribution:")
print(result_df["nearest_store_name"].value_counts())