# Import libraries
import pandas as pd
import glob
import os

# Define the folder path where the KNMI data is stored
folder_path = "data\\luchtmeetnet_csvs_enddate_dbscan\\NL*_VAL_PRE"

all_data = []

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
    
final_data = pd.concat(all_data, ignore_index=True, sort=True)

# Set time as index
final_data.set_index("time", inplace=True)

# Columns to aggregate
pollutant_cols = [
    'BC', 'CO', 'H2S', 'NH3', 'NOx', 'O3', 'Ox', 'SO2', 
    'ZWR', 'no2', 'no2.1', 'pm10', 'pm25'
]

meta_cols = ['location', 'longitude', 'latitude']

# Build aggregation dictionary
agg_dict = {col: "mean" for col in pollutant_cols if col in final_data.columns}
agg_dict.update({col: "first" for col in meta_cols if col in final_data.columns})

# Resample daily per station
daily_lucht = (
    final_data.groupby("location", group_keys=False)
               .resample("D")
               .agg(agg_dict)
               .reset_index()
)

daily_lucht.to_parquet("data/Luchtmeetnet_final_data.parquet", index=False)



