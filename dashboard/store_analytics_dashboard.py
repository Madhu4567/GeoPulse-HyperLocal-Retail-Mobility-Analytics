
from pathlib import Path

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[1]

DATA_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "consolidated_store_insights.csv"
)


st.set_page_config(
    page_title="GeoPulse Analytics",
    page_icon="📍",
    layout="wide"
)


@st.cache_data
def load_data():
    return pd.read_csv(DATA_FILE)


st.title("📍 GeoPulse – HyperLocal Retail Mobility Analytics")
st.caption("Retail Store Performance | Geographic Catchment | Device Mobility")

if not DATA_FILE.exists():
    st.error(f"Dataset not found: {DATA_FILE}")
    st.stop()

df = load_data()

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
