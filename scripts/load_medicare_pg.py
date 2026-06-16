"""
Carica medicare_providers.csv in PostgreSQL.
Prerequisito: il CSV deve essere già presente in data/medicare/
Uso: python scripts/load_medicare_pg.py
"""
import os
import psycopg2

PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_DB   = os.getenv("POSTGRES_DB", "healthdata")
PG_USER = os.getenv("POSTGRES_USER", "drill")
PG_PASS = os.getenv("POSTGRES_PASSWORD", "drill123")

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "medicare", "medicare_providers.csv")


def load() -> None:
    csv_path = os.path.abspath(CSV_PATH)
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV non trovato: {csv_path}\nEsegui prima: python scripts/download_datasets.py")

    conn = psycopg2.connect(host=PG_HOST, port=PG_PORT, dbname=PG_DB, user=PG_USER, password=PG_PASS)
    try:
        with conn, conn.cursor() as cur:
            cur.execute("TRUNCATE healthdata.medicare_providers;")
            with open(csv_path, encoding="utf-8") as f:
                cur.copy_expert(
                    "COPY healthdata.medicare_providers FROM STDIN WITH (FORMAT csv, HEADER true, DELIMITER ',')",
                    f
                )
            cur.execute("SELECT COUNT(*) FROM healthdata.medicare_providers;")
            count = cur.fetchone()[0]
            print(f"Caricati {count:,} record in healthdata.medicare_providers")
    finally:
        conn.close()


if __name__ == "__main__":
    load()
