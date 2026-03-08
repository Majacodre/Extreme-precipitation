import requests
import pandas as pd
from io import BytesIO
import pyarrow

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
    "aggregationType": "hour"
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

merge_air_data(data_storage_path)


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

get_pollutant(data_storage_path)