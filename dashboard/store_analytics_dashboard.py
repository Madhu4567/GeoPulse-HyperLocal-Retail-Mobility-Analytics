
from pathlib import Path

import pandas as pd
import streamlit as st

from src.data_quality.Day_13_validate_data import get_data_quality_report

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "consolidated_store_insights.csv"
)


st.set_page_config(
    page_title="GeoPulse Analytics",
    layout="wide"
)


@st.cache_data
def load_data():
    return pd.read_csv(DATA_FILE)


st.title(" GeoPulse – HyperLocal Retail Mobility Analytics")
st.caption("Retail Store Performance | Geographic Catchment | Device Mobility")

if not DATA_FILE.exists():
    st.error(f"Dataset not found: {DATA_FILE}")
    st.stop()

df = load_data()

# Data Quality Overview
st.header("Data Quality Overview")

quality_report = get_data_quality_report()

gps_report = quality_report["gps"]
store_report = quality_report["stores"]

q1, q2, q3, q4 = st.columns(4)

q1.metric("GPS Records", f"{gps_report['total_records']:,}")
q2.metric("Store Records", f"{store_report['total_records']:,}")

total_nulls = gps_report["null_values"] + store_report["null_values"]
total_duplicates = gps_report["duplicate_records"] + store_report["duplicate_records"]

q3.metric("Total Null Values", total_nulls)
q4.metric("Total Duplicate Records", total_duplicates)

if (
    gps_report["invalid_coordinates"] == 0
    and store_report["invalid_coordinates"] == 0
    and gps_report["invalid_timestamps"] == 0
    and total_nulls == 0
    and total_duplicates == 0
    and not gps_report["missing_columns"]
    and not store_report["missing_columns"]
    and not gps_report["invalid_data_types"]
    and not store_report["invalid_data_types"]
    and store_report["duplicate_store_ids"] == 0
):
    st.success("GPS and Store Data Quality: PASSED")
else:
    st.error("Data Quality Issues Detected")
# Detailed Data Quality Results

st.subheader("GPS Data Quality Details")

gps_col1, gps_col2, gps_col3, gps_col4 = st.columns(4)

gps_col1.metric("Missing Columns", len(gps_report["missing_columns"]))
gps_col2.metric("Null Values", gps_report["null_values"])
gps_col3.metric("Duplicate Records", gps_report["duplicate_records"])
gps_col4.metric("Invalid Coordinates", gps_report["invalid_coordinates"])

gps_col5, gps_col6 = st.columns(2)

gps_col5.metric("Invalid Timestamps", gps_report["invalid_timestamps"])
gps_col6.metric("Invalid Data Types", len(gps_report["invalid_data_types"]))

st.divider()

st.subheader("Store Data Quality Details")

store_col1, store_col2, store_col3, store_col4 = st.columns(4)

store_col1.metric("Missing Columns", len(store_report["missing_columns"]))
store_col2.metric("Null Values", store_report["null_values"])
store_col3.metric("Duplicate Records", store_report["duplicate_records"])
store_col4.metric("Duplicate Store IDs", store_report["duplicate_store_ids"])

store_col5, store_col6 = st.columns(2)

store_col5.metric("Invalid Coordinates", store_report["invalid_coordinates"])
store_col6.metric("Invalid Data Types", len(store_report["invalid_data_types"]))

st.divider()

# Sidebar filter
st.sidebar.header("Filters")

stores = ["All Stores"] + sorted(df["nearest_store_name"].unique())

selected_store = st.sidebar.selectbox(
    "Select Store",
    stores
)

if selected_store != "All Stores":
    filtered_df = df[
        df["nearest_store_name"] == selected_store
    ]
else:
    filtered_df = df.copy()

# KPI metrics
total_stores = filtered_df["nearest_store_id"].nunique()
total_pings = filtered_df["total_gps_pings"].sum()
total_devices = filtered_df["unique_devices"].sum()
avg_distance = filtered_df["average_distance_km"].mean()

st.subheader("Key Performance Indicators")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Stores", f"{total_stores}")
c2.metric("Assigned GPS Pings", f"{total_pings:,}")
c3.metric("Store-Device Associations", f"{total_devices:,}")
c4.metric("Average Distance", f"{avg_distance:.2f} km")

st.divider()

# Store performance
st.subheader("Store Performance")

performance = filtered_df[
    ["nearest_store_name", "total_gps_pings"]
].set_index("nearest_store_name")

st.bar_chart(performance)

# Peak hour analysis
st.subheader("Peak Hour Analysis")

peak_data = filtered_df[
    ["nearest_store_name", "peak_hour_gps_pings"]
].set_index("nearest_store_name")

st.bar_chart(peak_data)
# Catchment analysis
st.header("Store Catchment Analysis")

st.subheader("Catchment Distance Metrics")

avg_col, min_col, max_col = st.columns(3)

avg_col.metric(
    "Average Catchment Distance",
    f"{filtered_df['average_distance_km'].mean():.2f} km"
)

min_col.metric(
    "Minimum Catchment Distance",
    f"{filtered_df['minimum_distance_km'].min():.2f} km"
)

max_col.metric(
    "Maximum Catchment Distance",
    f"{filtered_df['maximum_distance_km'].max():.2f} km"
)

st.subheader("Catchment Distance Distribution")

catchment_columns = [
    "0-1 km",
    "1-3 km",
    "3-5 km",
    "Above 5 km"
]

catchment_data = filtered_df[
    ["nearest_store_name"] + catchment_columns
].set_index("nearest_store_name")

st.bar_chart(catchment_data)
# Overall Catchment Distribution Summary

st.subheader("Overall Catchment Distribution")

catchment_totals = catchment_data.sum()

summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)

for col, (band, count) in zip(
    [summary_col1, summary_col2, summary_col3, summary_col4],
    catchment_totals.items()
):
    col.metric(band, f"{count:,.0f}")
    
# Mobility analysis
st.subheader("Store Mobility Insights")

mobility_data = filtered_df[
    [
        "nearest_store_name",
        "multi_store_devices",
        "mobility_percentage"
    ]
].set_index("nearest_store_name")

st.dataframe(mobility_data, width="stretch")

# Complete dataset
st.subheader("Consolidated Store Analytics")

st.dataframe(filtered_df, width="stretch")

st.success("GeoPulse dashboard loaded successfully!")
