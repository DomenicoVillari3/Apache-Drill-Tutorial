"""
Scarica i 3 dataset da HealthData.gov / CMS / CDC via API Socrata.
Uso: python scripts/download_datasets.py
"""
import os
import requests

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

DATASETS = [
    {
        "name": "COVID-19 Hospital Capacity",
        "url": "https://healthdata.gov/resource/g62h-syeh.csv?$limit=100000",
        "path": os.path.join(DATA_DIR, "covid", "hospital_capacity.csv"),
    },
    {
        "name": "Medicare Provider Utilization & Payment",
        "url": "https://data.cms.gov/resource/fs4p-t5eq.csv?$limit=100000",
        "path": os.path.join(DATA_DIR, "medicare", "medicare_providers.csv"),
    },
    {
        "name": "NNDSS Notifiable Diseases",
        "url": "https://data.cdc.gov/resource/x9gk-5huc.json?$limit=50000",
        "path": os.path.join(DATA_DIR, "nndss", "diseases.json"),
    },
]


def download(name: str, url: str, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    print(f"Downloading {name}...")
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
    size_mb = os.path.getsize(path) / (1 << 20)
    print(f"  -> {path}  ({size_mb:.1f} MB)")


if __name__ == "__main__":
    for ds in DATASETS:
        download(ds["name"], ds["url"], ds["path"])
    print("\nDone. Run scripts/csv_to_parquet.py next.")
