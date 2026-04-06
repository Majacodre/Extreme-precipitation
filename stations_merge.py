# Import libraries
import pandas as pd
import numpy as np
import xarray as xr
from scipy.spatial import cKDTree

# Read data
KNMI_data = pd.read_parquet("data/KNMI_final_data.parquet")
Lucht_data = pd.read_parquet("data/Luchtmeetnet_final_data.parquet")

# Extract station information and find nearest stations
KNMI_stations = KNMI_data[["location", "latitude", "longitude"]].drop_duplicates().dropna().reset_index(drop=True)
KNMI_cords = KNMI_stations[["latitude", "longitude"]].to_numpy()
Lucht_stations = Lucht_data[["location", "latitude", "longitude"]].drop_duplicates().dropna().reset_index(drop=True)
Lucht_cords = Lucht_stations[["latitude", "longitude"]].to_numpy()

tree = cKDTree(Lucht_cords)
distances, indices = tree.query(KNMI_cords, k=1)

distances_km = distances * 111

nearest_stations = pd.DataFrame({
    "KNMI_station": KNMI_stations["location"],
    "KNMI_lat": KNMI_stations["latitude"],
    "KNMI_lon": KNMI_stations["longitude"],
    "Lucht_station": Lucht_stations.iloc[indices]["location"].values,
    "Lucht_lat": Lucht_stations.iloc[indices]["latitude"].values,
    "Lucht_lon": Lucht_stations.iloc[indices]["longitude"].values,
    "distance_km": distances_km
})


knmi_with_lucht = KNMI_data.merge(
    nearest_stations,
    left_on=["latitude", "longitude"],
    right_on=["KNMI_lat", "KNMI_lon"],
    how="left"
)

# Merge Lucht measurements using coordinates and time
final_df = knmi_with_lucht.merge(
    Lucht_data,
    left_on=["Lucht_lat", "Lucht_lon", "time"],
    right_on=["latitude", "longitude", "time"],
    how="left",
    suffixes=("_knmi", "_lucht")
)
# Save final dataset
final_df.to_parquet("data/full_dataset.parquet", index=False)