"""
Carica il dataset NNDSS in MongoDB e crea gli indici necessari.
Prerequisito: diseases.json già presente in data/nndss/
Uso: python init-mongo/01_load_nndss.py
"""
import json
import os
import sys
from pymongo import MongoClient, ASCENDING

MONGO_URI = os.getenv("MONGO_URI", "mongodb://drill:drill123@localhost:27017/")
DB_NAME   = os.getenv("MONGO_DB", "healthdata")
JSON_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "nndss", "diseases.json")


def load(client: MongoClient) -> None:
    db  = client[DB_NAME]
    col = db["nndss"]

    # Svuota la collection se esiste già (idempotente)
    col.drop()

    # Legge il JSON (array di documenti)
    with open(JSON_PATH, encoding="utf-8") as f:
        documents = json.load(f)

    if not documents:
        print("ERRORE: il file JSON è vuoto.", file=sys.stderr)
        sys.exit(1)

    result = col.insert_many(documents)
    print(f"Inseriti {len(result.inserted_ids):,} documenti in {DB_NAME}.nndss")

    # Indici per le query Drill e per le aggregazioni nel notebook
    col.create_index([("reporting_area", ASCENDING)], name="idx_area")
    col.create_index([("disease_name",   ASCENDING)], name="idx_disease")
    col.create_index(
        [("mmwr_year", ASCENDING), ("mmwr_week", ASCENDING)],
        name="idx_mmwr"
    )
    print("Indici creati: idx_area, idx_disease, idx_mmwr")

    print(f"Conteggio finale: {col.count_documents({}):,} documenti")


if __name__ == "__main__":
    with MongoClient(MONGO_URI) as client:
        load(client)
