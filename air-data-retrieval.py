import requests
import pandas as pd
from io import BytesIO
import pyarrow
import geopandas as gpd

data_storage_path = "./data"

def retrieve_air_data():
  # Base API
  BASE_URL = "https://eeadmz1-downloads-api-appservice.azurewebsites.net"

  body_request = {
    "countries": ["NL"],
    "cities": [],
    "dataset": 2,
    "pollutants": [],
    "dateTimeStart": "2013-01-01T00:00:00Z",
    "dateTimeEnd": "2025-12-31T23:59:59Z",
    "aggregationType": "day"
  }

  response = requests.post(f"{BASE_URL}/ParquetFile/urls", json=body_request)

  if response.ok:
      urls = response.text 
      
      with open(f"{data_storage_path}/urls.txt", "w") as file:
          file.write(urls)
  else:
      print("Error:", response.status_code, response.text)

def merge_air_data(data_storage_path):

    output_file = f"{data_storage_path}/netherlands_air_quality_2013_2025.parquet"

    with open(f"{data_storage_path}/urls.txt", "r") as file:
        urls = file.read().splitlines()

    # Create empty dataframe list (memory-safe chunking)
    merged_data = []
    missing_urls = []

    for url in urls:
        try:
            print(f"Fetching data from {url}...")

            response = requests.get(url, timeout=60)

            if response.status_code != 200:
                print(f"fetching {url}, status code {response.status_code}")
                continue

            df_chunk = pd.read_parquet(BytesIO(response.content))

            merged_data.append(df_chunk)

        except Exception as e:
            print(f"Error processing {url}: {e}")
            missing_urls.append(url)
            continue

    if len(merged_data) == 0:
        return "No data was merged."

    print("Merging chunks...")

    final_df = pd.concat(merged_data, ignore_index=True)

    print("Sorting dataset...")

    if "dateTime" in final_df.columns:
        final_df = final_df.sort_values("dateTime")
        print("Dataset sorted by dateTime.")
    else:
        print("dateTime column not found. Skipping sorting.")

    print("Saving parquet file...")

    final_df.to_parquet(output_file, index=False)

    print("saving missing urls...")

    with open(f"{data_storage_path}/missing_urls.txt", "w") as file:
        for url in missing_urls:
            file.write(url + "\n")

    return "All data merged and saved successfully!"

def get_pollutant(data_storage_path):   
    
    url = "https://eeadmz1-downloads-api-appservice.azurewebsites.net/pollutant"

    response = requests.get(url)
    response.raise_for_status()

    data = response.json()

    pollutans = []

    for item in data:
        pollutans.append({
            "notation": item["notation"],
            "id": item["id"],
            "pk": item["pk"],
            "code": item["code"]
        })

    print("saving pollutans...")
    df_pollutans = pd.DataFrame(pollutans)
    df_pollutans.to_parquet(f"{data_storage_path}/pollutants.parquet", index=False)
    print("pollutans saved successfully!")

def get_stations(data_storage_path):
    url = (
    "https://air.discomap.eea.europa.eu/arcgis/rest/services/"
    "AirQuality/AirQualityDownloadServiceEUMonitoringStations/MapServer/0/query?"
    "where=CountryCode%20%3D%20'NL'&outFields=*&outSR=4326&f=geojson"
    )

    resp = requests.get(url)
    gdf_eea = gpd.read_file(resp.text)

    # Extract lat/lon and station code
    gdf_eea['lat'] = gdf_eea.geometry.y
    gdf_eea['lon'] = gdf_eea.geometry.x
    eea_stations = gdf_eea[['AirQualityStationEoICode', 'lat', 'lon', 'AQStationName']].copy()
    eea_stations = eea_stations.reset_index(drop=True)
    
    print("EEA stations NL:", eea_stations.shape[0])

    # Save to CSV
    if data_storage_path:
        eea_stations.to_csv(f"{data_storage_path}/eea_stations.csv", index=False)
        print(f"Saved EEA stations to {data_storage_path}")

def main ():

    # Step 1: Retrieve and merge air quality data
    print("Retrieving and merging air quality data...")

    retrieve_air_data()
    merge_air_data(data_storage_path)

    # Step 2: Get pollutant and station metadata
    print("Retrieving pollutant and station metadata...")

    get_pollutant(data_storage_path)
    get_stations(data_storage_path)

    # Step 3: Load data 
    print("Loading data...")

    air_df = pd.read_parquet(f"{data_storage_path}/netherlands_air_quality_2013_2025.parquet")
    pollutants_df = pd.read_parquet(f"{data_storage_path}/pollutants.parquet")
    eea_stations = pd.read_csv(f"{data_storage_path}/eea_stations.csv")

    # Step 4: Data merging
    print("Merging datasets...")

    # Extract station_id from Samplingpoint column
    air_df["station_id"] = air_df["Samplingpoint"].str.extract(r'(NL\d+)')

    # Merge
    air_df = air_df.merge(pollutants_df[["notation", "pk"]], left_on = "Pollutant", right_on = "pk", how="left")
    air_df = air_df.merge(eea_stations, left_on = "station_id", right_on = "AirQualityStationEoICode", how="left")

    print("Data merged successfully!")

    air_df.to_parquet(f"{data_storage_path}/air_quality_2013_2025_full_dataset.parquet", index=False)

    print("Full dataset saved successfully!")

main()