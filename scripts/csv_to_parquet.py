#hospital_capacity.csv in Parquet columnar con pyarrow.

import os
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

BASE = os.path.join(os.path.dirname(__file__), "..")
SRC  = os.path.join(BASE, "data", "covid", "hospital_capacity.csv")
DST  = os.path.join(BASE, "data", "covid_parquet", "hospital_capacity.parquet")

NUMERIC_COLS = [
    "inpatient_beds_used_covid",
    "inpatient_beds",
    "adult_icu_beds_used",
    "staffed_icu_beds_utilization",
]


def convert() -> None:
    print(f"Reading {SRC}...")
    df = pd.read_csv(SRC, low_memory=False)
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(",", "", regex=False),
                errors="coerce",
            )

    os.makedirs(os.path.dirname(DST), exist_ok=True)
    table = pa.Table.from_pandas(df)
    pq.write_table(table, DST, compression="snappy")

    src_mb = os.path.getsize(SRC) / (1 << 20)
    dst_mb = os.path.getsize(DST) / (1 << 20)

    print(f"CSV:{src_mb:.1f} MB")
    print(f"Parquet: {dst_mb:.1f} MB")
    print(f"Rows: {len(df):,}  Columns:{len(df.columns)}")


if __name__ == "__main__":
    convert()
