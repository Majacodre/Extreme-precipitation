# Extreme-precipitation

## Overview

This repository contains data processing, station matching, and analysis code for a thesis project on Dutch extreme precipitation and environmental station data. It combines KNMI weather station observations with Luchtmeetnet measurement stations, performs daily aggregation, and merges the datasets for downstream analysis.

## Repository Structure

- `KNMI_merge.py`: Aggregate KNMI station files into daily weather measurements and save `data/KNMI_final_data.parquet`.
- `Luchtmeetnet_merge.py`: Aggregate Luchtmeetnet station files into daily pollutant averages and save `data/Luchtmeetnet_final_data.parquet`.
- `stations_merge.py`: Match KNMI stations to nearest Luchtmeetnet stations, merge the daily datasets, and save `data/full_dataset.parquet` and `data/station_mapping.parquet`.
- `Exploratory Data Analysis.ipynb`: Notebook for exploration of merged data and preliminary insights.
- `modelling&interpolation.ipynb`: Notebook for modeling and interpolation experiments related to extreme precipitation analysis.
- `data/`: Data folder containing raw station directories, intermediate parquet outputs, and LaTeX tables for report results.

## Requirements

Recommended Python packages:

- `pandas`
- `numpy`
- `scipy`
- `pyarrow`

If using the repository virtual environment, activate it first. Example:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install pandas numpy scipy pyarrow
```

## Usage

1. Make sure raw data folders exist in `data/KNMI/` and `data/luchtmeetnet_csvs_enddate_dbscan/`.
2. Generate aggregated KNMI data:

```powershell
python KNMI_merge.py
```

3. Generate aggregated Luchtmeetnet data:

```powershell
python Luchtmeetnet_merge.py
```

4. Merge the two datasets by nearest station and daily date:

```powershell
python stations_merge.py
```

5. Open the notebooks for analysis:

- `Exploratory Data Analysis.ipynb`
- `modelling&interpolation.ipynb`

## Output Files

- `data/KNMI_final_data.parquet`
- `data/Luchtmeetnet_final_data.parquet`
- `data/full_dataset.parquet`
- `data/station_mapping.parquet`

## Notes

- The scripts expect paired CSV and JSON files inside each station folder.
- Aggregation rules are defined in the scripts and handle negative or invalid sensor values by converting them to missing data.
- Station matching uses a nearest neighbor search in geographic coordinates and converts degree distances to approximate kilometers.
- The raw datasets referenced in `.gitignore` are not included in this repository and are available to download from the following link: `https://amsuni-my.sharepoint.com/:u:/g/personal/maja_kubara_student_uva_nl/IQBXzaRFlv_MTYDyPGkhzErNAaSkSaUIfEtzLuzTKY1bMrs?e=PHNfjY`.


