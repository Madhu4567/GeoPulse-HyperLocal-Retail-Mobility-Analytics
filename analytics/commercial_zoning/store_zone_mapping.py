"""
GeoPulse Store-to-Zone Spatial Mapping Engine
Associates retail stores with their containing commercial zone polygon via
point-in-polygon spatial evaluation, preserving unmatched stores.
"""
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
import pandas as pd

import sys
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.settings import PATHS
from analytics.commercial_zoning.zone_validator import point_in_polygon
from analytics.commercial_zoning.zone_generator import ZONE_DEFINITIONS, generate_commercial_zones


class StoreZoneMapper:
    """Maps retail stores to commercial zones using point-in-polygon geometry testing."""

    def __init__(self, zone_definitions: Optional[List[Dict[str, Any]]] = None):
        self.zone_definitions = zone_definitions or ZONE_DEFINITIONS

    def map_stores(self, stores_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Perform spatial containment join between stores and zones."""
        if len(stores_df) == 0:
            raise ValueError("Input stores dataframe is empty.")

        mapped_records = []

        for _, store in stores_df.iterrows():
            sid = store["store_id"]
            sname = store["store_name"]
            scat = store.get("store_category", "Retail")
            lat = float(store["latitude"])
            lon = float(store["longitude"])
            status = store.get("store_status", "active")

            matched_zone = None
            for z in self.zone_definitions:
                if point_in_polygon(lat, lon, z["coordinates"]):
                    matched_zone = z
                    break

            if matched_zone:
                mapped_records.append({
                    "store_id": sid,
                    "store_name": sname,
                    "store_category": scat,
                    "latitude": lat,
                    "longitude": lon,
                    "store_status": status,
                    "zone_id": matched_zone["zone_id"],
                    "zone_name": matched_zone["zone_name"],
                    "zone_type": matched_zone["zone_type"],
                    "is_within_zone": True,
                })
            else:
                mapped_records.append({
                    "store_id": sid,
                    "store_name": sname,
                    "store_category": scat,
                    "latitude": lat,
                    "longitude": lon,
                    "store_status": status,
                    "zone_id": "UNZONED",
                    "zone_name": "Outside Commercial Zones",
                    "zone_type": "Unassigned",
                    "is_within_zone": False,
                })

        mapped_df = pd.DataFrame(mapped_records)
        mapped_df = mapped_df.sort_values(by="store_id").reset_index(drop=True)

        summary = {
            "total_stores": len(mapped_df),
            "stores_inside_zones": int(mapped_df["is_within_zone"].sum()),
            "stores_outside_zones": int((~mapped_df["is_within_zone"]).sum()),
            "zone_store_distribution": mapped_df.groupby("zone_name")["store_id"].count().to_dict(),
        }

        return mapped_df, summary

    def save(self, df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
        out_p = output_path or (PATHS["data_processed"] / "store_zone_mapping.csv")
        out_p.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_p, index=False)
        return out_p


def map_stores_to_zones(
    stores_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    s_path = stores_path or (PATHS["data_processed"] / "cleaned_store_locations.csv")
    if not s_path.exists():
        s_path = PATHS["data_reference"] / "store_locations.csv"
        if not s_path.exists():
            raise FileNotFoundError(f"Store locations file not found at {s_path}.")

    stores_df = pd.read_csv(s_path)
    mapper = StoreZoneMapper()
    mapped_df, summary = mapper.map_stores(stores_df)
    saved_p = mapper.save(mapped_df, output_path)

    print(f"[StoreZoneMapper] Mapped {summary['total_stores']} stores -> {summary['stores_inside_zones']} inside commercial zones, {summary['stores_outside_zones']} unzoned.")
    print(f"  Saved to: {saved_p}")
    return mapped_df, summary


if __name__ == "__main__":
    map_stores_to_zones()
