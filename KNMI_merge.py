# Import libraries
import pandas as pd
import glob
import os
import numpy as np

# Define the folder path where the KNMI data is stored
folder_path = "data/KNMI/KNMI_*"

all_data = []

# Custom function to get mode, if multiple modes exist take first
def mode_or_first(x):
    if len(x) == 0:
        return None
    m = x.mode()
    if len(m) > 0:
        return m.iloc[0]
    return None

# Loop through each folder and read the CSV and JSON files, then merge the data
for path in glob.glob(folder_path):

    csv_files = glob.glob(os.path.join(path, "*.csv"))
    json_files = glob.glob(os.path.join(path, "*.json"))

    csv_data = pd.read_csv(csv_files[0], sep=",")
    csv_data["time"] = pd.to_datetime(csv_data["time"], unit = 's', errors="coerce")

    json_data = pd.read_json(json_files[0])
    location = json_data["location"].iloc[0]
    longitude = json_data["longitude"].iloc[0]
    latitude = json_data["latitude"].iloc[0]

    csv_data["location"] = location
    csv_data["longitude"] = longitude
    csv_data["latitude"] = latitude

    all_data.append(csv_data)
    
final_data = pd.concat(all_data, ignore_index=True)

# Aggregate by day and station
sum_cols = ["RH", "DR", "SQ", "Q"]         
mean_cols = ["temp", "TD", "FF", "FH", "P", "N", "DD", "rh", "M", "R", "S", "O", "Y"] 
max_cols = ["FX"]          
min_cols = ["T10N"]              
first_cols = ["location", "longitude", "latitude"] 
mode = ["WW", "IX", "VV"] 
none_negative = ["RH", "DR", "SQ", "Q", "FF", "FH", "P", "N", "rh", "FX"]

# Ensure all numeric columns are properly converted to numeric types and there are no values below 0 before aggregation
numeric_cols = sum_cols + mean_cols + max_cols + min_cols

for col in numeric_cols:
    if col in final_data.columns:
        final_data[col] = pd.to_numeric(final_data[col], errors="coerce")

final_data[none_negative] = final_data[none_negative].mask(final_data[none_negative] < 0, np.nan)

# Build aggregation dictionary
agg_dict = {col: "sum" for col in sum_cols if col in final_data.columns}
agg_dict.update({col: "mean" for col in mean_cols if col in final_data.columns})
agg_dict.update({col: "min" for col in min_cols if col in final_data.columns})
agg_dict.update({col: "max" for col in max_cols if col in final_data.columns})
agg_dict.update({col: "first" for col in first_cols if col in final_data.columns})
agg_dict.update({col: mode_or_first for col in mode if col in final_data.columns})

final_data["date"] = pd.to_datetime(final_data["time"]).dt.floor("D")

daily_knmi = (
    final_data
    .groupby(["location", "longitude", "latitude", "date"], as_index=False)
    .agg(agg_dict)
)

daily_knmi.to_parquet("data/KNMI_final_data.parquet", index=False)



