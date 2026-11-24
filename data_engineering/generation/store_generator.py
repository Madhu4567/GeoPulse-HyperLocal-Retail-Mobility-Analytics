"""
GeoPulse Retail Store Location Generator
Generates realistic synthetic retail store locations with categories and coordinates.
"""
from pathlib import Path
from typing import Dict, List, Optional
import random
import pandas as pd
import numpy as np

import sys
# Ensure project root is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.settings import DATA_CONFIG, PATHS


# Core retail sub-districts in study area (Manhattan Core) with cluster weights
RETAIL_HUBS = [
    {"name": "Midtown / Herald Square", "lat": 40.7505, "lon": -73.9890, "weight": 0.25},
    {"name": "SoHo Retail District", "lat": 40.7233, "lon": -73.9985, "weight": 0.20},
    {"name": "Union Square / Flatiron", "lat": 40.7380, "lon": -73.9895, "weight": 0.20},
    {"name": "Upper East Side Commercial", "lat": 40.7735, "lon": -73.9565, "weight": 0.15},
    {"name": "Financial District", "lat": 40.7085, "lon": -74.0090, "weight": 0.10},
    {"name": "Chelsea / Meatpacking", "lat": 40.7420, "lon": -74.0048, "weight": 0.10},
]

STORE_BRAND_TEMPLATES = {
    "Grocery": ["FreshMarket", "WholeGreens", "UrbanPantry", "MetroGrocer", "TraderPoint"],
    "Fashion": ["AuraApparel", "UrbanThread", "VelocityWear", "NordicStyle", "ZaraPoint"],
    "Electronics": ["CircuitHub", "ApexTech", "DigitalBazaar", "ByteSpace", "AppleSphere"],
    "Pharmacy": ["CarePlus Pharmacy", "MetroRx", "HealthFirst", "Walgreens Corner", "DuaneRx"],
    "Convenience": ["7-Express", "BodegaCentral", "QuickStop", "CityCorner", "CornerMart"],
    "Department Store": ["Macy Plaza", "Bloomington Galleria", "Barneys Corner", "Hudson Emporium"],
    "Cafe & Bakery": ["Roast & Bean", "BlueMist Coffee", "UrbanBrew", "BakeryLoft", "DailyGrind"],
}


class StoreDataGenerator:
    """Generates synthetic retail store locations clustered within retail commercial zones."""

    def __init__(
        self,
        num_stores: int = DATA_CONFIG["default_num_stores"],
        random_seed: int = DATA_CONFIG["random_seed"],
        categories: Optional[List[str]] = None,
    ):
        self.num_stores = num_stores
        self.random_seed = random_seed
        self.categories = categories or DATA_CONFIG["store_categories"]
        random.seed(self.random_seed)
        np.random.seed(self.random_seed)

    def generate(self) -> pd.DataFrame:
        """Generate synthetic store locations dataset."""
        stores: List[Dict] = []
        hub_weights = [hub["weight"] for hub in RETAIL_HUBS]

        for i in range(1, self.num_stores + 1):
            store_id = f"STR_{i:03d}"
            category = random.choice(self.categories)
            brand = random.choice(STORE_BRAND_TEMPLATES.get(category, ["RetailHub"]))
            hub = random.choices(RETAIL_HUBS, weights=hub_weights, k=1)[0]

            # Store coordinate with small Gaussian dispersion around hub center (~200m to 800m)
            # 0.001 deg lat approx 111m, 0.001 deg lon approx 85m at 40N
            lat_offset = np.random.normal(0, 0.004)
            lon_offset = np.random.normal(0, 0.004)
            lat = round(float(hub["lat"] + lat_offset), 6)
            lon = round(float(hub["lon"] + lon_offset), 6)

            # Ensure coordinates are within overall study bounds
            lat = max(DATA_CONFIG["lat_min"], min(DATA_CONFIG["lat_max"], lat))
            lon = max(DATA_CONFIG["lon_min"], min(DATA_CONFIG["lon_max"], lon))

            store_name = f"{brand} - {hub['name'].split('/')[0].strip()}"
            status = random.choices(["active", "inactive"], weights=[0.93, 0.07], k=1)[0]

            stores.append({
                "store_id": store_id,
                "store_name": store_name,
                "store_category": category,
                "latitude": lat,
                "longitude": lon,
                "store_status": status,
            })

        df = pd.DataFrame(stores)
        return df

    def save(self, df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
        """Save stores dataframe to CSV."""
        path = output_path or (PATHS["data_reference"] / "store_locations.csv")
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)
        return path


def generate_synthetic_stores(
    num_stores: int = DATA_CONFIG["default_num_stores"],
    output_path: Optional[Path] = None,
    random_seed: int = DATA_CONFIG["random_seed"],
) -> pd.DataFrame:
    """Helper function to generate and persist store locations."""
    generator = StoreDataGenerator(num_stores=num_stores, random_seed=random_seed)
    df = generator.generate()
    saved_path = generator.save(df, output_path=output_path)
    print(f"[StoreDataGenerator] Generated {len(df)} retail stores saved to {saved_path}")
    return df


if __name__ == "__main__":
    generate_synthetic_stores()
