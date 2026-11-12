
from pathlib import Path
import pandas as pd
import numpy as np

# Project root directory
BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUT_DIR = BASE_DIR / "data" / "raw"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Reproducible random data
rng = np.random.default_rng(42)

# Generate 20 synthetic stores around Bengaluru
num_stores = 20

stores = pd.DataFrame({
    "store_id": [f"S{i:03d}" for i in range(1, num_stores + 1)],
    "store_name": [f"Store_{i}" for i in range(1, num_stores + 1)],
    "latitude": rng.uniform(12.90, 13.05, num_stores),
    "longitude": rng.uniform(77.50, 77.70, num_stores)
})

# Save store locations
output_file = OUTPUT_DIR / "store_locations.csv"
stores.to_csv(output_file, index=False)

print(f"Successfully generated {len(stores)} stores")
print(f"Saved to: {output_file}")
print(stores.head())



# Generate synthetic GPS pings for 100 devices

num_devices = 100
pings_per_device = 50

device_ids = [
    f"D{i:03d}" for i in range(1, num_devices + 1)
]

gps_data = []

for device_id in device_ids:
    # Random starting location around Bengaluru
    base_lat = rng.uniform(12.90, 13.05)
    base_lon = rng.uniform(77.50, 77.70)

    for ping_num in range(pings_per_device):
        gps_data.append({
            "device_id": device_id,
            "latitude": base_lat + rng.normal(0, 0.002),
            "longitude": base_lon + rng.normal(0, 0.002),
            "timestamp": (
                pd.Timestamp("2026-11-12 08:00:00")
                + pd.Timedelta(minutes=ping_num * 5)
            )
        })

gps_df = pd.DataFrame(gps_data)

# Save GPS ping data
gps_output = OUTPUT_DIR / "gps_pings.csv"
gps_df.to_csv(gps_output, index=False)

print(f"Successfully generated {len(gps_df)} GPS pings")
print(f"Saved to: {gps_output}")
print(gps_df.head())



# Basic data validation

print("\n--- DATA VALIDATION ---")

# Store validation
assert stores["store_id"].nunique() == 20
assert stores["latitude"].between(-90, 90).all()
assert stores["longitude"].between(-180, 180).all()

print("Store validation: PASSED")

# GPS validation
assert len(gps_df) == 5000
assert gps_df["device_id"].nunique() == 100
assert gps_df["latitude"].between(-90, 90).all()
assert gps_df["longitude"].between(-180, 180).all()
assert gps_df["timestamp"].notna().all()

print("GPS validation: PASSED")

# Duplicate validation
print("Duplicate GPS records:", gps_df.duplicated().sum())

print("\nAll basic validations completed!")
