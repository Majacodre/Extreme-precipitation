# Import libraries
import pandas as pd
import numpy as np
import xarray as xr
from scipy.spatial import cKDTree

# Read data
eea_data = pd.read_parquet("data/air_quality_2013_2025_full_dataset.parquet")
eea_stations = pd.read_csv("data/eea_stations.csv")
KNMI = xr.open_dataset("data/KIS___OPER_P___OBS_____L2.nc", decode_cf=True, mask_and_scale=True)
KNMI_2013 = KNMI.sel(time=KNMI.time >= np.datetime64("2013-01-01"))

# Find nearest stations 
eea_stations = eea_stations[["AirQualityStationEoICode", "lat", "lon"]].drop_duplicates().reset_index(drop=True)
KNMI_stations = KNMI_2013[['station','lat','lon']].to_dataframe().reset_index()
KNMI_stations = KNMI_stations[['station','lat','lon']].drop_duplicates().reset_index(drop=True)

eea_cords = eea_stations[["lat", "lon"]].to_numpy()
knmi_cords = KNMI_stations[["lat", "lon"]].to_numpy()

tree = cKDTree(knmi_cords)
distances, indices = tree.query(eea_cords, k = 1)
distances_km = distances * 111

nearest_stations = pd.DataFrame({
    "AirQualityStationEoICode": eea_stations["AirQualityStationEoICode"],
    "nearest_KNMI_station": KNMI_stations.iloc[indices]["station"].values,
    "distance_km": distances_km
})

# Merge data based on day and nearest station
KNMI_df = KNMI_2013.to_dataframe().reset_index()
eea_data = eea_data.merge(nearest_stations, left_on="station_id", right_on="AirQualityStationEoICode", how="left")
final_df = eea_data.merge(KNMI_df, left_on=["nearest_KNMI_station", "Start"], right_on=["station", "time"], how="left")

# Save final dataset
final_df.to_parquet("data/air_quality_with_meteorological_data.parquet", index=False)