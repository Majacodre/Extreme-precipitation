import logging
import sys
from datetime import datetime, timezone
import requests
import os

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel("INFO")


class OpenDataAPI:
    def __init__(self, api_token: str):
        self.base_url = "https://api.dataplatform.knmi.nl/open-data/v1"
        self.headers = {"Authorization": api_token}

    def __get_data(self, url, params=None):
        return requests.get(url, headers=self.headers, params=params).json()

    def list_files(self, dataset_name: str, dataset_version: str, params: dict):
        return self.__get_data(
            f"{self.base_url}/datasets/{dataset_name}/versions/{dataset_version}/files",
            params=params,
        )

    def get_file_url(self, dataset_name: str, dataset_version: str, file_name: str):
        return self.__get_data(
            f"{self.base_url}/datasets/{dataset_name}/versions/{dataset_version}/files/{file_name}/url"
        )


def download_file_from_temporary_download_url(download_url, filename):
    try:
        os.makedirs("data", exist_ok=True)

        filepath = os.path.join("data", filename)

        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()

            with open(filepath, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        logger.info(f"Successfully downloaded dataset file to {filepath}")

    except Exception:
        logger.exception("Unable to download dataset file using download URL")
        sys.exit(1)


def main():

    api_key = "eyJvcmciOiI1ZTU1NGUxOTI3NGE5NjAwMDEyYTNlYjEiLCJpZCI6ImZiNmM2MmI1NzZkYjRmODg5YjQxMjA2NDAzNGU1YTJkIiwiaCI6Im11cm11cjEyOCJ"

    dataset_name = "etmaalgegevensKNMIstations"
    dataset_version = "1"

    api = OpenDataAPI(api_token=api_key)

    start_date = datetime(2013, 1, 1).date()
    end_date = datetime.now(timezone.utc).date()

    logger.info(f"Fetching dataset {dataset_name} from {start_date} to {end_date}")

    params = {
        "orderBy": "created",
        "maxKeys": 100
    }

    next_page_token = None
    files_downloaded = 0

    while True:

        if next_page_token:
            params["pageToken"] = next_page_token

        response = api.list_files(dataset_name, dataset_version, params)
        print(response)

        if "files" not in response:
            logger.error("Invalid API response")
            break

        files = response["files"]

        for file in files:

            filename = file["filename"]

            # ---- Extract date from filename ----
            try:
                date_str = filename.split("_")[-1].replace(".nc", "")
                file_date = datetime.strptime(date_str, "%Y%m%d").date()
            except Exception:
                logger.warning(f"Cannot parse date from filename {filename}")
                continue

            # ---- Date filtering ----
            if file_date < start_date:
                logger.info("Reached files older than 2013-01-01. Stopping.")
                return

            if file_date > end_date:
                continue

            logger.info(f"Downloading {filename}")

            file_url_resp = api.get_file_url(
                dataset_name,
                dataset_version,
                filename
            )

            download_file_from_temporary_download_url(
                file_url_resp["temporaryDownloadUrl"],
                filename
            )

            files_downloaded += 1

        next_page_token = response.get("nextPageToken")

        if not next_page_token:
            break

    logger.info(f"Total downloaded files: {files_downloaded}")

if __name__ == "__main__":
    main()