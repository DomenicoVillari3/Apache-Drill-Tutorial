"""
Rinomina le colonne dei dataset con spazi/mixed-case in snake_case.
Output: file *_clean.csv pronti per COPY (Postgres) e mongoimport (MongoDB).

Uso: python3 scripts/normalize_columns.py
     (dalla root del progetto)
"""

import csv
import os

# ---------------------------------------------------------------------------
# Mapping colonne
# ---------------------------------------------------------------------------

DATASET2_MAP = {
    "state": "state",
    "collection_date":   "collection_date",
    "Inpatient Beds Occupied by COVID-19 Patients Estimated":  "estimated_beds_covid",
    "Count LL":  "count_ll",
    "Count UL": "count_ul",
    "Percentage of Inpatient Beds Occupied by COVID-19 Patients Estimated": "pct_beds_covid",
    "Percentage LL":   "pct_ll",
    "Percentage UL":  "pct_ul",
    "Total Inpatient Beds":    "total_inpatient_beds",
    "Total LL": "total_ll",
    "Total UL":   "total_ul",
    "geocoded_state":  "geocoded_state",
}

DATASET3_MAP = {
    "Provider Name": "provider_name",
    "Address1":  "address1",
    "Address2":  "address2",
    "City":  "city",
    "County": "county",
    "State Code":   "state",
    "Zip":    "zip",
    "National Drug Code": "national_drug_code",
    "Order Label":"order_label",
    "Courses Available": "courses_available",
    "Geocoded Address": "geocoded_address",
    "NPI":   "npi",
    "Last Report Date": "last_report_date",
    "Provider Status":  "provider_status",
    "Provider Note":    "provider_note",
}

DATASET5_MAP = {
    "Provider Name": "provider_name",
    "Address 1":   "address1",
    "Address 2":   "address2",
    "City":        "city",
    "State":       "state",
    "Zip":         "zip",
    "Public Phone Number":   "public_phone",
    "Public Website":        "public_website",
    "Latitude":    "latitude",
    "Longitude":   "longitude",
    "Geopoint":    "geopoint",
    "Last Report Date":      "last_report_date",
    "Is PAP Site": "is_pap_site",
    "Is Telehealth Site":    "is_telehealth_site",
    "Telehealth Website":    "telehealth_website",
    "Pharmacist Prescribing": "pharmacist_prescribing",
    "Home Delivery":         "home_delivery",
    "Home Delivery URL":     "home_delivery_url",
    "Is T2T Site": "is_t2t_site",
    "Is ICATT Site":         "is_icatt_site",
    "Has USG Product":       "has_usg_product",
    "Has Commercial Product": "has_commercial_product",
    "Has Paxlovid":          "has_paxlovid",
    "Has Commercial Paxlovid": "has_commercial_paxlovid",
    "Has USG Paxlovid":      "has_usg_paxlovid",
    "Has Lagevrio":          "has_lagevrio",
    "Has Commercial Lagevrio": "has_commercial_lagevrio",
    "Has USG Lagevrio":      "has_usg_lagevrio",
    "Has Veklury": "has_veklury",
    "Grantee Code":          "grantee_code",
    "Provider Note":         "provider_note",
}

# Campi numerici del Dataset 2 che contengono virgola come separatore migliaia
DATASET2_NUMERIC = {
    "estimated_beds_covid", "count_ll", "count_ul",
    "pct_beds_covid", "pct_ll", "pct_ul",
    "total_inpatient_beds", "total_ll", "total_ul",
}

# Dataset 1: nessun mapping colonne (resta grezzo apposta, vedi Query 1 nel
# notebook per la dimostrazione di schema-on-read). Puliamo solo la colonna
# usata da ogni altra query (Q4a-Q4f, Q6), cosi' quelle query non devono piu'
# ripetere REPLACE/NULLIF/CAST ad ogni FROM.
DATASET1_NUMERIC = {"inpatient_beds_used_covid"}


def clean_value(col_name: str, value: str, numeric_fields: set) -> str:
    if col_name in numeric_fields and value:
        return value.replace(",", "")
    return value


# ---------------------------------------------------------------------------
# Lavoro
# ---------------------------------------------------------------------------

jobs = [
    (
        "Dataset 2 — Estimated Beds (→ PostgreSQL)",
        "data/estimated_beds/estimated_beds.csv",
        "data/estimated_beds/estimated_beds_clean.csv",
        DATASET2_MAP,
        DATASET2_NUMERIC,
        True,
    ),
    (
        "Dataset 3 — Therapeutic Locator (→ MongoDB)",
        "data/therapeutic/therapeutic_locator.csv",
        "data/therapeutic/therapeutic_locator_clean.csv",
        DATASET3_MAP,
        set(),
        True,
    ),
    (
        "Dataset 5 — Treatments (dfs CSV)",
        "data/treatments/treatments.csv",
        "data/treatments/treatments_clean.csv",
        DATASET5_MAP,
        set(),
        True,
    ),
    (
        "Dataset 1 — Hospital Capacity (dfs CSV, numbers only)",
        "data/covid/hospital_capacity.csv",
        "data/covid/hospital_capacity_clean.csv",
        {},
        DATASET1_NUMERIC,
        False,
    ),
]

for name, src, dst, col_map, numeric_fields, warn_unmapped in jobs:
    if not os.path.exists(src):
        print(f"[SKIP] {name}: file non trovato ({src})")
        continue

    with open(src, newline="", encoding="utf-8") as fin, \
         open(dst, "w", newline="", encoding="utf-8") as fout:

        reader = csv.DictReader(fin)
        original_cols = reader.fieldnames or []

        if warn_unmapped:
            unmapped = [c for c in original_cols if c not in col_map]
            if unmapped:
                print(f"[WARN] {name}: colonne senza mapping (lasciate invariate): {unmapped}")

        new_cols = [col_map.get(c, c) for c in original_cols]
        writer = csv.DictWriter(fout, fieldnames=new_cols)
        writer.writeheader()

        for row in reader:
            new_row = {
                col_map.get(k, k): clean_value(col_map.get(k, k), v, numeric_fields)
                for k, v in row.items()
            }
            writer.writerow(new_row)

    size_mb = os.path.getsize(dst) / (1024 * 1024)
    print(f"[OK]   {name}")
    print(f"       {src} → {dst}  ({size_mb:.2f} MB)")
    print(f"       Colonne: {original_cols} → {new_cols}\n")
