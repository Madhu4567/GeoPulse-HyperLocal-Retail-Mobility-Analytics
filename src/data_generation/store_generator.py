"""Scaffold compatibility wrapper for store generator."""
from data_engineering.generation.store_generator import (
    StoreDataGenerator,
    generate_synthetic_stores,
)

__all__ = ["StoreDataGenerator", "generate_synthetic_stores"]

if __name__ == "__main__":
    generate_synthetic_stores()
