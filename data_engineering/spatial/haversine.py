"""
GeoPulse Haversine Distance Engine
Provides high-performance scalar and vectorized great-circle distance calculations
using the spherical law of haversines.
"""
from typing import Union
import numpy as np

# Mean volumetric Earth radius in kilometers (IUGG recommended value)
EARTH_RADIUS_KM = 6371.0088


def haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    radius: float = EARTH_RADIUS_KM,
) -> float:
    """Calculate the great-circle distance between two geographic coordinates in kilometers.

    Parameters:
        lat1, lon1: First coordinate pair in decimal degrees.
        lat2, lon2: Second coordinate pair in decimal degrees.
        radius: Earth radius in kilometers (default: 6371.0088 km).

    Returns:
        Great-circle distance in kilometers.
    """
    if any(np.isnan([lat1, lon1, lat2, lon2])):
        return float("nan")

    # Convert decimal degrees to radians
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)

    # Haversine formula
    a = np.sin(delta_phi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))

    return float(radius * c)


def haversine_vectorized(
    lat1: Union[np.ndarray, float],
    lon1: Union[np.ndarray, float],
    lat2: Union[np.ndarray, float],
    lon2: Union[np.ndarray, float],
    radius: float = EARTH_RADIUS_KM,
) -> np.ndarray:
    """Vectorized calculation of great-circle distance across arrays of coordinates.
    Supports broadcasting between (N, 1) and (1, M) coordinates.

    Parameters:
        lat1, lon1: First set of coordinates (scalar, 1D array, or 2D array).
        lat2, lon2: Second set of coordinates (scalar, 1D array, or 2D array).
        radius: Earth radius in kilometers.

    Returns:
        NumPy array of distances in kilometers matching broadcast shape.
    """
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)

    a = np.sin(delta_phi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))

    return radius * c


if __name__ == "__main__":
    # Benchmark against known coordinates:
    # Empire State Building: 40.748817, -73.985428
    # Times Square: 40.758896, -73.985130
    dist = haversine_distance(40.748817, -73.985428, 40.758896, -73.985130)
    print(f"Empire State to Times Square distance: {dist:.4f} km (Expected ~1.12 km)")

    # London (51.5074, -0.1278) to Paris (48.8566, 2.3522)
    dist_lp = haversine_distance(51.5074, -0.1278, 48.8566, 2.3522)
    print(f"London to Paris distance: {dist_lp:.2f} km (Expected ~343-344 km)")
