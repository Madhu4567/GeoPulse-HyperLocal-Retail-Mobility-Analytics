"""
GeoPulse Commercial Zone Generator
Defines and generates realistic, non-overlapping commercial geographic zones
aligned with retail store hubs in the Manhattan study area.
"""
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import json
from datetime import datetime
import pandas as pd

import sys
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.settings import PATHS
from analytics.commercial_zoning.zone_validator import geodesic_polygon_area_sq_km, validate_commercial_zones


# Definition of 6 primary retail commercial zones in Manhattan study area
# Vertices defined as list of (latitude, longitude) tuples, closed ring.
ZONE_DEFINITIONS = [
    {
        "zone_id": "ZN_001",
        "zone_name": "Midtown / Herald Square Retail Core",
        "zone_type": "Shopping District",
        # 34th St to 42nd St, Broadway to 6th Ave corridor
        "coordinates": [
            (40.7460, -73.9930),
            (40.7555, -73.9930),
            (40.7555, -73.9820),
            (40.7460, -73.9820),
            (40.7460, -73.9930),
        ],
    },
    {
        "zone_id": "ZN_002",
        "zone_name": "SoHo Historic Commercial Corridor",
        "zone_type": "Main Market",
        # Houston to Canal, West Broadway to Crosby
        "coordinates": [
            (40.7180, -74.0040),
            (40.7280, -74.0040),
            (40.7280, -73.9930),
            (40.7180, -73.9930),
            (40.7180, -74.0040),
        ],
    },
    {
        "zone_id": "ZN_003",
        "zone_name": "Union Square / Flatiron Hub",
        "zone_type": "Mixed Commercial-Residential Area",
        # 14th St to 23rd St, 5th Ave to Park Ave S
        "coordinates": [
            (40.7330, -73.9950),
            (40.7430, -73.9950),
            (40.7430, -73.9840),
            (40.7330, -73.9840),
            (40.7330, -73.9950),
        ],
    },
    {
        "zone_id": "ZN_004",
        "zone_name": "Financial District Commerce Center",
        "zone_type": "Business District",
        # Wall St, Fulton, Battery Park corridor
        "coordinates": [
            (40.7040, -74.0150),
            (40.7130, -74.0150),
            (40.7130, -74.0030),
            (40.7040, -74.0030),
            (40.7040, -74.0150),
        ],
    },
    {
        "zone_id": "ZN_005",
        "zone_name": "Upper East Side Luxury Corridor",
        "zone_type": "Retail Complex",
        # 68th to 80th St, Madison to Lexington
        "coordinates": [
            (40.7680, -73.9630),
            (40.7790, -73.9630),
            (40.7790, -73.9500),
            (40.7680, -73.9500),
            (40.7680, -73.9630),
        ],
    },
    {
        "zone_id": "ZN_006",
        "zone_name": "Chelsea / Meatpacking Highline District",
        "zone_type": "Local Market",
        # 14th St to 22nd St, 9th Ave to 11th Ave
        "coordinates": [
            (40.7370, -74.0110),
            (40.7470, -74.0110),
            (40.7470, -73.9990),
            (40.7370, -73.9990),
            (40.7370, -74.0110),
        ],
    },
]


def coords_to_wkt(coords: List[Tuple[float, float]]) -> str:
    """Convert (lat, lon) list to WKT POLYGON((lon lat, ...))."""
    wkt_pts = [f"{lon:.6f} {lat:.6f}" for lat, lon in coords]
    return f"POLYGON(({', '.join(wkt_pts)}))"


def coords_to_geojson_geometry(coords: List[Tuple[float, float]]) -> Dict[str, Any]:
    """Convert (lat, lon) list to GeoJSON geometry object with [lon, lat] coordinates."""
    geojson_ring = [[lon, lat] for lat, lon in coords]
    return {
        "type": "Polygon",
        "coordinates": [geojson_ring],
    }


class CommercialZoneGenerator:
    """Generates validated commercial zone records, WKT representations, and GeoJSON outputs."""

    def __init__(self, raw_definitions: Optional[List[Dict[str, Any]]] = None):
        self.raw_definitions = raw_definitions or ZONE_DEFINITIONS

    def generate(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Validate definitions and build DataFrame + GeoJSON feature collection."""
        # 1. Geometric & boundary validation
        val_summary = validate_commercial_zones(self.raw_definitions)
        if not val_summary["all_zones_valid"]:
            raise ValueError(f"Zone validation failed: {val_summary}")

        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        records = []
        geojson_features = []

        for z in self.raw_definitions:
            coords = z["coordinates"]
            area_sq_km = geodesic_polygon_area_sq_km(coords)
            wkt_geom = coords_to_wkt(coords)
            geojson_geom = coords_to_geojson_geometry(coords)

            records.append({
                "zone_id": z["zone_id"],
                "zone_name": z["zone_name"],
                "zone_type": z["zone_type"],
                "geometry": wkt_geom,
                "area_sq_km": area_sq_km,
                "created_at": now_str,
            })

            geojson_features.append({
                "type": "Feature",
                "id": z["zone_id"],
                "properties": {
                    "zone_id": z["zone_id"],
                    "zone_name": z["zone_name"],
                    "zone_type": z["zone_type"],
                    "area_sq_km": area_sq_km,
                },
                "geometry": geojson_geom,
            })

        df = pd.DataFrame(records)
        geojson_collection = {
            "type": "FeatureCollection",
            "features": geojson_features,
            "crs": {
                "type": "name",
                "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
            },
        }

        return df, geojson_collection

    def save(
        self,
        df: pd.DataFrame,
        geojson_data: Dict[str, Any],
        output_csv: Optional[Path] = None,
        output_geojson: Optional[Path] = None,
    ) -> Tuple[Path, Path]:
        csv_p = output_csv or (PATHS["data_reference"] / "commercial_zones.csv")
        geojson_p = output_geojson or (PATHS["data_reference"] / "commercial_zones.geojson")

        csv_p.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(csv_p, index=False)

        with open(geojson_p, "w", encoding="utf-8") as f:
            json.dump(geojson_data, f, indent=2)

        return csv_p, geojson_p


def generate_commercial_zones(
    output_csv: Optional[Path] = None,
    output_geojson: Optional[Path] = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    generator = CommercialZoneGenerator()
    df, geojson_data = generator.generate()
    csv_p, geo_p = generator.save(df, geojson_data, output_csv, output_geojson)
    print(f"[CommercialZoneGenerator] Generated {len(df)} zones.")
    print(f"  CSV: {csv_p}")
    print(f"  GeoJSON: {geo_p}")
    return df, geojson_data


if __name__ == "__main__":
    generate_commercial_zones()
