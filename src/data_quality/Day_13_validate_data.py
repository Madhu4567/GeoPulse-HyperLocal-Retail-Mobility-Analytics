
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"


def validate_columns(df, required_columns):
    missing_columns = [
        col for col in required_columns if col not in df.columns
    ]

    return missing_columns


def validate_nulls(df):
    return df.isnull().sum()


def validate_duplicates(df):
    return df.duplicated().sum()


def validate_coordinates(df):
    invalid_latitude = ~df["latitude"].between(-90, 90)
    invalid_longitude = ~df["longitude"].between(-180, 180)


    return (invalid_latitude | invalid_longitude).sum()


def validate_timestamps(df):
    timestamps = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    return timestamps.isna().sum()


def validate_gps_data_types(df):
    expected_types = {
        "device_id": "object",
        "latitude": "float64",
        "longitude": "float64",
        "timestamp": "object"
    }

    invalid_types = {}

    for column, expected_type in expected_types.items():
        actual_type = str(df[column].dtype)

        if actual_type != expected_type:
            invalid_types[column] = {
                "expected": expected_type,
                "actual": actual_type
            }

    return invalid_types


def validate_store_data_types(df):
    expected_types = {
        "store_id": "object",
        "store_name": "object",
        "latitude": "float64",
        "longitude": "float64"
    }

    invalid_types = {}

    for column, expected_type in expected_types.items():
        actual_type = str(df[column].dtype)

        if actual_type != expected_type:
            invalid_types[column] = {
                "expected": expected_type,
                "actual": actual_type
            }

    return invalid_types



def validate_gps_data():
    file_path = RAW_DIR / "gps_pings.csv"

    df = pd.read_csv(file_path)
    invalid_types = validate_gps_data_types(df)

    required_columns = [
        "device_id",
        "latitude",
        "longitude",
        "timestamp"
    ]

    missing_columns = validate_columns(df, required_columns)
    null_counts = validate_nulls(df)
    duplicate_count = validate_duplicates(df)
    invalid_coordinates = validate_coordinates(df)
    invalid_timestamps = validate_timestamps(df)

    print("\n========== GPS DATA QUALITY REPORT ==========")

    print(f"Total Records: {len(df)}")
    print(f"Missing Columns: {missing_columns}")
    print(f"Null Values:\n{null_counts}")
    print(f"Duplicate Records: {duplicate_count}")
    print(f"Invalid Coordinates: {invalid_coordinates}")
    print(f"Invalid Timestamps: {invalid_timestamps}")
    print(f"Invalid Data Types: {invalid_types}")

    passed = (
        not missing_columns
        and null_counts.sum() == 0
        and invalid_timestamps == 0
        and duplicate_count == 0
        and invalid_coordinates == 0
        and len(invalid_types) == 0
        
    )

    print("\nValidation Status:", "PASSED" if passed else "FAILED")

    return passed

def validate_store_data():
    file_path = RAW_DIR / "store_locations.csv"

    df = pd.read_csv(file_path)

    required_columns = [
        "store_id",
        "store_name",
        "latitude",
        "longitude"
    ]

    missing_columns = validate_columns(df, required_columns)
    null_counts = validate_nulls(df)
    duplicate_count = validate_duplicates(df)

    duplicate_store_ids = (
        df["store_id"].duplicated().sum()
        if "store_id" in df.columns else 0
    )

    invalid_coordinates = validate_coordinates(df)
    invalid_types = validate_store_data_types(df)

    print("\n========== STORE DATA QUALITY REPORT ==========")

    print(f"Total Stores: {len(df)}")
    print(f"Missing Columns: {missing_columns}")
    print(f"Null Values:\n{null_counts}")
    print(f"Duplicate Records: {duplicate_count}")
    print(f"Duplicate Store IDs: {duplicate_store_ids}")
    print(f"Invalid Coordinates: {invalid_coordinates}")
    print(f"Invalid Data Types: {invalid_types}")

    passed = (
        not missing_columns
        and null_counts.sum() == 0
        and duplicate_count == 0
        and duplicate_store_ids == 0
        and invalid_coordinates == 0
        and len(invalid_types) == 0
    )

    print("\nValidation Status:", "PASSED" if passed else "FAILED")

    return passed



if __name__ == "__main__":
    gps_status = validate_gps_data()
    store_status = validate_store_data()

    print("\n========== FINAL DATA QUALITY STATUS ==========")

    if gps_status and store_status:
        print("ALL DATA QUALITY CHECKS PASSED")
    else:
        print("DATA QUALITY VALIDATION FAILED")



