# Import libraries
import pandas as pd
import glob
import os

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
    csv_data["time"] = pd.to_datetime(csv_data["time"], unit="s")

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

agg_dict = {col: "sum" for col in sum_cols if col in final_data.columns}
agg_dict.update({col: "mean" for col in mean_cols if col in final_data.columns})
agg_dict.update({col: "min" for col in min_cols if col in final_data.columns})
agg_dict.update({col: "max" for col in max_cols if col in final_data.columns})
agg_dict.update({col: "first" for col in first_cols if col in final_data.columns})
agg_dict.update({col: mode_or_first for col in mode if col in final_data.columns})

final_data = final_data.set_index("time")
daily_knmi = (
    final_data.groupby("location", group_keys=False)
              .resample("D")
              .agg(agg_dict)
              .reset_index()
)

daily_knmi.to_parquet("data/KNMI_final_data.parquet", index=False)



