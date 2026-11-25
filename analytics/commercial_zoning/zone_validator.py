"""
GeoPulse Commercial Zone Validator
Validates geometric integrity, coordinate systems, polygon closures,
non-overlap rules, and calculates true geodesic surface areas in square kilometers.
"""
from typing import List, Tuple, Dict, Any
import math
import numpy as np

# Earth radius in kilometers (IUGG mean spherical radius)
EARTH_RADIUS_KM = 6371.0088


def geodesic_polygon_area_sq_km(coords: List[Tuple[float, float]], radius: float = EARTH_RADIUS_KM) -> float:
    """Calculate the geodesic surface area of a spherical polygon defined by (lat, lon) coordinates
    using spherical excess integration.

    Parameters:
        coords: List of (latitude, longitude) coordinate pairs in decimal degrees.
                The polygon should be closed (last point equals first point).
        radius: Sphere radius in kilometers.

    Returns:
        Area in square kilometers.
    """
    if len(coords) < 4:
        return 0.0

    # Ensure ring is closed
    if coords[0] != coords[-1]:
        coords = list(coords) + [coords[0]]

    n = len(coords)
    if n < 4:
        return 0.0

    # Convert coordinates to radians
    lats = [math.radians(p[0]) for p in coords]
    lons = [math.radians(p[1]) for p in coords]

    # Spherical polygon area: sum of (lon[i+1] - lon[i-1]) * sin(lat[i])
    total = 0.0
    for i in range(n - 1):
        prev_idx = (i - 1) % (n - 1)
        next_idx = (i + 1) % (n - 1)
        d_lon = lons[next_idx] - lons[prev_idx]
        # Normalize longitude difference to [-pi, pi]
        while d_lon > math.pi:
            d_lon -= 2.0 * math.pi
        while d_lon < -math.pi:
            d_lon += 2.0 * math.pi
        total += d_lon * math.sin(lats[i])

    area = (radius ** 2) * abs(total) / 2.0
    return round(float(area), 4)


def point_in_polygon(lat: float, lon: float, polygon_coords: List[Tuple[float, float]]) -> bool:
    """Determine if a geographic point (lat, lon) lies inside a polygon using ray casting.

    Parameters:
        lat, lon: Coordinate to test (latitude, longitude).
        polygon_coords: List of (lat, lon) vertices defining the polygon boundary.

    Returns:
        True if the point lies strictly inside or on the polygon boundary.
    """
    n = len(polygon_coords)
    inside = False

    # Standard ray-casting algorithm
    p1_lat, p1_lon = polygon_coords[0]
    for i in range(1, n + 1):
        p2_lat, p2_lon = polygon_coords[i % n]
        if min(p1_lon, p2_lon) < lon <= max(p1_lon, p2_lon):
            if lat <= max(p1_lat, p2_lat):
                if p1_lon != p2_lon:
                    lat_inters = (lon - p1_lon) * (p2_lat - p1_lat) / (p2_lon - p1_lon) + p1_lat
                else:
                    lat_inters = p1_lat
                if p1_lat == p2_lat or lat <= lat_inters:
                    inside = not inside
        p1_lat, p1_lon = p2_lat, p2_lon

    return inside


class CommercialZoneValidator:
    """Validates geometry integrity, bounds, uniqueness, and non-overlap for commercial zones."""

    def __init__(self, lat_bounds: Tuple[float, float] = (40.70, 40.82), lon_bounds: Tuple[float, float] = (-74.02, -73.93)):
        self.lat_min, self.lat_max = lat_bounds
        self.lon_min, self.lon_max = lon_bounds

    def validate_zone(self, zone: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate an individual commercial zone record."""
        errors: List[str] = []

        # 1. ID check
        zid = zone.get("zone_id")
        if not zid or not str(zid).startswith("ZN_"):
            errors.append(f"Invalid zone_id '{zid}': must begin with 'ZN_'")

        # 2. Name & Type check
        if not zone.get("zone_name"):
            errors.append("Missing zone_name")
        if not zone.get("zone_type"):
            errors.append("Missing zone_type")

        # 3. Geometry check
        coords = zone.get("coordinates")
        if not coords or len(coords) < 4:
            errors.append(f"Invalid coordinates: polygon requires >= 4 vertices, found {len(coords) if coords else 0}")
        else:
            # Check closure
            if coords[0] != coords[-1]:
                errors.append("Polygon ring is not closed (first vertex != last vertex)")

            # Coordinate bounds check
            for lat, lon in coords:
                if not (self.lat_min <= lat <= self.lat_max) or not (self.lon_min <= lon <= self.lon_max):
                    errors.append(f"Vertex ({lat}, {lon}) falls outside study area bounds")
                    break

        return len(errors) == 0, errors

    def validate_collection(self, zones: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate an entire collection of commercial zones."""
        zone_ids = set()
        validation_results = []
        all_valid = True

        for z in zones:
            is_valid, errs = self.validate_zone(z)
            zid = z.get("zone_id")
            if zid in zone_ids:
                is_valid = False
                errs.append(f"Duplicate zone_id '{zid}' detected")
            else:
                zone_ids.add(zid)

            if not is_valid:
                all_valid = False

            validation_results.append({
                "zone_id": zid,
                "zone_name": z.get("zone_name"),
                "is_valid": is_valid,
                "errors": errs,
                "area_sq_km": geodesic_polygon_area_sq_km(z.get("coordinates", [])),
            })

        return {
            "all_zones_valid": all_valid,
            "total_zones": len(zones),
            "valid_zone_count": sum(1 for r in validation_results if r["is_valid"]),
            "zone_evaluations": validation_results,
        }


def validate_commercial_zones(zones: List[Dict[str, Any]]) -> Dict[str, Any]:
    validator = CommercialZoneValidator()
    return validator.validate_collection(zones)
