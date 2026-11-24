"""Scaffold compatibility wrapper for spatial processing."""
from data_engineering.spatial.haversine import haversine_distance, haversine_vectorized
from data_engineering.spatial.nearest_store import NearestStoreMapper, map_nearest_stores
from data_engineering.spatial.visit_detection import StoreVisitDetector, detect_store_visits

__all__ = [
    "haversine_distance",
    "haversine_vectorized",
    "NearestStoreMapper",
    "map_nearest_stores",
    "StoreVisitDetector",
    "detect_store_visits",
]
