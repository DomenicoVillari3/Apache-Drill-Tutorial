import csv
import os
import sys
from pymongo import MongoClient, ASCENDING

MONGO_URI  = os.getenv("MONGO_URI", "mongodb://drill:drill123@localhost:27017/")
DB_NAME    = os.getenv("MONGO_DB", "healthdata")
CSV_PATH   = os.path.join(os.path.dirname(__file__), "..", "data", "therapeutic", "therapeutic_locator_clean.csv")

NUMERIC_FIELDS = {"courses_available"}


def parse_row(row: dict) -> dict:
    for field in NUMERIC_FIELDS:
        if field in row and row[field] not in ("", None):
            try:
                row[field] = float(row[field])
            except ValueError:
                pass
    return row


def load(client: MongoClient) -> None:
    db  = client[DB_NAME]
    col = db["therapeutic"]

    col.drop()

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        documents = [parse_row(dict(row)) for row in reader]

    if not documents:
        print("ERRORE: il file CSV è vuoto.", file=sys.stderr)
        sys.exit(1)

    result = col.insert_many(documents)
    print(f"Inseriti {len(result.inserted_ids):,} documenti in {DB_NAME}.therapeutic")

    col.create_index([("state",           ASCENDING)], name="idx_state")
    col.create_index([("provider_status", ASCENDING)], name="idx_status")
    col.create_index([("order_label",     ASCENDING)], name="idx_order")
    print("Indici creati: idx_state, idx_status, idx_order")

    print(f"Conteggio finale: {col.count_documents({}):,} documenti")


if __name__ == "__main__":
    with MongoClient(MONGO_URI) as client:
        load(client)
