import csv
import json
import os

datasets = [
    ("Dataset 1 — Hospital Capacity (dfs CSV)",    "data/covid/hospital_capacity.csv",            "csv"),
    ("Dataset 2 — Estimated Beds (→ PostgreSQL)",  "data/estimated_beds/estimated_beds.csv",       "csv"),
    ("Dataset 3 — Therapeutic Locator (→ MongoDB)","data/therapeutic/therapeutic_locator.csv",     "csv"),
    ("Dataset 4 — Community Profile County (dfs)", "data/county/community_profile.csv",            "csv"),
    ("Dataset 5 — Treatments (dfs CSV)",           "data/treatments/treatments.csv",               "csv"),
]

for name, path, kind in datasets:
    if not os.path.exists(path):
        print(f"\n=== {name} ===")
        print(f"  [SKIP] File non trovato: {path}")
        continue

    size_mb = os.path.getsize(path) / (1024 * 1024)
    print(f"\n=== {name} ===")
    print(f"File   : {path}")
    print(f"Peso   : {size_mb:.2f} MB")

    if kind == "csv":
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            cols = next(reader)
            rows = sum(1 for _ in reader)
        print(f"Righe  : {rows:,}")
        print(f"Colonne: {len(cols)}")
        print(f"Campi  : {cols}")
    else:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        cols = list(d[0].keys()) if d else []
        print(f"Documenti: {len(d):,}")
        print(f"Campi (1° doc): {len(cols)} — {cols}")
