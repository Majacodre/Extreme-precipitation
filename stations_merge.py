# Import libraries
import pandas as pd
import numpy as np
from scipy.spatial import cKDTree

# Read data
KNMI_data = pd.read_parquet("data/KNMI_final_data.parquet")
Lucht_data = pd.read_parquet("data/Luchtmeetnet_final_data.parquet")

KNMI_stations = (
    KNMI_data[["location", "latitude", "longitude"]]
    .drop_duplicates()
    .dropna()
    .reset_index(drop=True)
)

Lucht_stations = (
    Lucht_data[["latitude", "longitude"]]
    .drop_duplicates()
    .dropna()
    .reset_index(drop=True)
)

# Assign stable station IDs to Lucht stations - working around missing location names
Lucht_stations["lucht_station_id"] = Lucht_stations.index

#cDKTree for nearest neighbor search
KNMI_coords = KNMI_stations[["latitude", "longitude"]].to_numpy()
Lucht_coords = Lucht_stations[["latitude", "longitude"]].to_numpy()

tree = cKDTree(Lucht_coords)
distances, indices = tree.query(KNMI_coords, k=1)

# Convert approximate degrees to km 
distances_km = distances * 111

# Create a DataFrame to store the mapping
nearest_stations = pd.DataFrame({
    "KNMI_station": KNMI_stations["location"],
    "lucht_station_id": indices,
    "distance_km": distances_km
})

# Attach mapping to KNMI data
knmi_with_lucht = KNMI_data.merge(
    nearest_stations,
    left_on="location",
    right_on="KNMI_station",
    how="left"
)

# Attach mapping to Lucht data
Lucht_data = Lucht_data.merge(
    Lucht_stations,
    on=["latitude", "longitude"],
    how="left"
)

# final merge on station ID and time
final_df = knmi_with_lucht.merge(
    Lucht_data,
    on=["lucht_station_id", "date"],
    how="left",
    suffixes=("_knmi", "_lucht")
)

# Save the final merged dataset
final_df.to_parquet("data/full_dataset.parquet", index=False)
nearest_stations.to_parquet("data/station_mapping.parquet", index=False)