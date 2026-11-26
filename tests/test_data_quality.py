
import pandas as pd

from src.data_quality.Day_13_validate_data import (
    validate_columns,
    validate_nulls,
    validate_duplicates,
    validate_coordinates,
    validate_timestamps,
    validate_gps_data_types,
    validate_store_data_types,
)


def test_validate_columns():
    df = pd.DataFrame({"device_id": ["D1"], "latitude": [17.0]})
    result = validate_columns(df, ["device_id", "latitude", "timestamp"])
    assert result == ["timestamp"]


def test_validate_nulls():
    df = pd.DataFrame({"name": ["A", None, "C"]})
    result = validate_nulls(df)
    assert result["name"] == 1


def test_validate_duplicates():
    df = pd.DataFrame({"id": [1, 2, 2]})
    assert validate_duplicates(df) == 1


def test_validate_coordinates():
    df = pd.DataFrame({
        "latitude": [17.0, 95.0, 18.0],
        "longitude": [78.0, 80.0, 200.0]
    })
    assert validate_coordinates(df) == 2


def test_validate_timestamps():
    df = pd.DataFrame({
        "timestamp": ["2026-11-25 10:00:00", "invalid-date"]
    })
    assert validate_timestamps(df) == 1


def test_validate_gps_data_types():
    df = pd.DataFrame({
        "device_id": ["D1"],
        "latitude": [17.0],
        "longitude": [78.0],
        "timestamp": ["2026-11-25 10:00:00"]
    })
    assert validate_gps_data_types(df) == {}


def test_validate_store_data_types():
    df = pd.DataFrame({
        "store_id": ["S1"],
        "store_name": ["Store A"],
        "latitude": [17.0],
        "longitude": [78.0]
    })
    assert validate_store_data_types(df) == {}
