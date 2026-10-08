# Apache Drill Tutorial: query federate su dati sanitari

Questo progetto mostra come usare **Apache Drill 1.21.0** come motore SQL federato per interrogare e combinare dati eterogenei senza centralizzarli in un unico database.

Il caso di studio usa cinque dataset COVID-19 di HealthData.gov distribuiti tra:

- file CSV e Parquet, tramite il plugin `dfs`;
- PostgreSQL, tramite il plugin JDBC `pg`;
- MongoDB, tramite il plugin `mongo`.

La query principale esegue un join tra capacità ospedaliera, stime dei posti letto e centri terapeutici attivi usando un'unica istruzione SQL.

## Architettura

```mermaid
flowchart LR
    J[Jupyter<br/>:8888] -->|REST API| D[Apache Drill 1.21<br/>:8047 / :31010]
    D -->|dfs| F[CSV e Parquet]
    D -->|JDBC| P[PostgreSQL 15<br/>:5432]
    D -->|plugin mongo| M[MongoDB 6<br/>:27017]
    A[pgAdmin<br/>:5050] --> P
    X[mongo-express<br/>:8081] --> M
```

Tutti i servizi vengono avviati da Docker Compose sulla rete `health-net`. Drill non memorizza i dati: legge ogni sorgente attraverso gli storage plugin definiti in [`drill-config/storage-plugins.conf`](drill-config/storage-plugins.conf).

## Prerequisiti

- Docker Desktop con Docker Compose;
- Python 3.10 o successivo per preparare e caricare i dati;
- almeno 12 GB di memoria disponibile per Docker, in base ai limiti configurati per Drill;
- `curl` per scaricare il driver JDBC.

I dataset e i file JAR sono esclusi da Git. Devono quindi essere aggiunti localmente prima del primo avvio.

## Avvio rapido

### 1. Scaricare il driver PostgreSQL

Dalla root del repository:

```bash
mkdir -p jdbc-drivers
curl -L -o jdbc-drivers/postgresql-42.7.3.jar \
  https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.3/postgresql-42.7.3.jar
```

### 2. Scaricare i dataset

Esportare manualmente in formato CSV i dataset completi dalle rispettive pagine HealthData.gov:

```bash
mkdir -p data
```

| Dataset | Destinazione finale | Sorgente usata da Drill |
| --- | --- | --- |
| [Hospital Capacity State Timeseries](https://healthdata.gov/Hospital/COVID-19-Reported-Patient-Impact-and-Hospital-Capa/g62h-syeh/explore/page/filter) | `data/covid/hospital_capacity.csv` | `dfs` |
| [Estimated Inpatient Beds State Timeseries](https://healthdata.gov/dataset/COVID-19-Estimated-Inpatient-Beds-Occupied-by-COVI/py8k-j5rq/about_data) | `data/estimated_beds/estimated_beds.csv` | PostgreSQL |
| [Public Therapeutic Locator](https://healthdata.gov/Health/COVID-19-Public-Therapeutic-Locator/rxn6-qnx8/about_data) | `data/therapeutic/therapeutic_locator.csv` | MongoDB |
| [Community Profile Report — County Level](https://healthdata.gov/dataset/COVID-19-Community-Profile-Report-County-Level/di4u-7yu6/about_data) | `data/county/community_profile.csv` | `dfs` |
| [COVID-19 Treatments](https://healthdata.gov/ASPR/COVID-19-Treatments/xkzp-zhs7/about_data) | `data/treatments/treatments.csv` | `dfs` |

Le API Socrata possono restituire solo una parte dei dati senza token; per riprodurre l'analisi servono gli export completi. I nomi scaricati contengono in genere una data. Impostare `DATE` con il suffisso presente nei file:

```bash
DATE=20260617

mkdir -p data/raw data/covid data/covid_parquet data/county \
  data/estimated_beds data/therapeutic data/treatments

cp "data/COVID-19_Reported_Patient_Impact_and_Hospital_Capacity_by_State_Timeseries_(RAW)_${DATE}.csv" \
  data/covid/hospital_capacity.csv
cp "data/COVID-19_Estimated_Inpatient_Beds_Occupied_by_COVID-19_Patients_by_State_Timeseries_${DATE}.csv" \
  data/estimated_beds/estimated_beds.csv
cp "data/COVID-19_Public_Therapeutic_Locator_${DATE}.csv" \
  data/therapeutic/therapeutic_locator.csv
cp "data/COVID-19_Community_Profile_Report_-_County-Level_${DATE}.csv" \
  data/county/community_profile.csv
cp "data/COVID-19_Treatments_${DATE}.csv" \
  data/treatments/treatments.csv

mv data/COVID-19_*.csv data/raw/
```

### 3. Preparare i dati

Creare un ambiente Python e installare le dipendenze utilizzate dagli script:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install pandas pyarrow pymongo
```

Normalizzare le colonne, generare la versione Parquet e controllare i dataset:

```bash
python scripts/normalize_columns.py
python scripts/csv_to_parquet.py
python scripts/inspect_datasets.py
```

La copia CSV originale di Hospital Capacity resta disponibile per mostrare lo schema-on-read. La versione Parquet consente invece di confrontare parsing, compressione e prestazioni di un formato colonnare.

### 4. Avviare i servizi

```bash
docker compose up -d
docker compose ps
```

Attendere che `postgres` e `mongo` risultino `healthy`. Il primo avvio deve scaricare le immagini e può richiedere alcuni minuti.

### 5. Caricare PostgreSQL e MongoDB

La definizione della tabella PostgreSQL viene eseguita automaticamente solo quando il volume viene creato. I comandi seguenti funzionano anche con volumi già esistenti e rendono il caricamento ripetibile:

```bash
docker exec -i postgres psql -U drill -d healthdata \
  < init-sql/01_load_estimated_beds.sql

docker cp data/estimated_beds/estimated_beds_clean.csv \
  postgres:/tmp/estimated_beds_clean.csv

docker exec postgres psql -U drill -d healthdata -c \
  "\copy healthdata.estimated_beds FROM '/tmp/estimated_beds_clean.csv' CSV HEADER;"

python init-mongo/01_load_therapeutic.py
```

Verificare i record caricati:

```bash
docker exec postgres psql -U drill -d healthdata -c \
  "SELECT COUNT(*), MIN(collection_date), MAX(collection_date) FROM healthdata.estimated_beds;"

docker exec mongo mongosh \
  "mongodb://drill:drill123@localhost:27017/healthdata?authSource=admin" \
  --quiet --eval "db.therapeutic.countDocuments({})"
```

## Eseguire le query

Aprire la [Drill Web UI](http://localhost:8047), selezionare **Query** ed eseguire il test:

```sql
SELECT * FROM sys.version;
```

Le sette query dimostrative complete sono in [`queries/demo_queries.sql`](queries/demo_queries.sql). Copiarle nella Web UI singolarmente: il percorso copre schema-on-read, aggregazioni sulle singole sorgenti, join federato, confronto CSV/Parquet e analisi a granularità statale e di contea.

Esempio di accesso alle tre sorgenti:

```sql
SELECT * FROM dfs.healthdata.`covid/hospital_capacity.csv` LIMIT 5;
SELECT * FROM pg.healthdata.estimated_beds LIMIT 5;
SELECT * FROM mongo.healthdata.therapeutic LIMIT 5;
```

## Notebook e interfacce

| Servizio | URL | Uso |
| --- | --- | --- |
| Apache Drill | <http://localhost:8047> | Query, storage plugin e profili |
| JupyterLab | <http://localhost:8888> | Notebook di analisi e grafici |
| pgAdmin | <http://localhost:5050> | Amministrazione PostgreSQL |
| mongo-express | <http://localhost:8081> | Esplorazione MongoDB |

Il notebook [`notebooks/analysis.ipynb`](notebooks/analysis.ipynb) interroga Drill attraverso la REST API, misura le query su più esecuzioni e genera i grafici di confronto. Jupyter è configurato senza token perché l'ambiente è pensato esclusivamente per uso locale.

## Struttura del repository

```text
.
├── data/                 # CSV e Parquet locali, non versionati
├── drill-config/         # configurazione degli storage plugin
├── init-mongo/           # caricamento della collection therapeutic
├── init-sql/             # schema PostgreSQL
├── jdbc-drivers/         # driver JDBC locale, non versionato
├── notebooks/            # analisi, benchmark e grafici
├── queries/              # query SQL dimostrative
├── report/               # relazione e immagini prodotte
├── scripts/              # ispezione, normalizzazione e conversione
├── commands.txt          # sequenza operativa estesa
└── docker-compose.yml    # stack locale completo
```

## Configurazione

Docker Compose usa questi valori predefiniti:

```dotenv
POSTGRES_DB=healthdata
POSTGRES_USER=drill
POSTGRES_PASSWORD=drill123
MONGO_DB=healthdata
MONGO_USER=drill
MONGO_PASSWORD=drill123
```

È possibile sovrascriverli in `.env`, ma le connessioni in `drill-config/storage-plugins.conf` e i comandi di caricamento devono essere aggiornati con gli stessi valori. Le credenziali predefinite e le interfacce senza autenticazione sono adatte solo a un ambiente locale di sviluppo.

## Arresto e pulizia

Arrestare i container mantenendo i dati persistenti:

```bash
docker compose down
```

Per ricreare PostgreSQL e MongoDB da zero, eliminare anche i volumi:

```bash
docker compose down -v
```

Il secondo comando cancella i dati caricati nei database; i file presenti nella directory locale `data/` non vengono rimossi.

## Approfondimenti

- [`commands.txt`](commands.txt): comandi operativi dettagliati;
- [`report/report.tex`](report/report.tex): relazione completa, architettura, risultati e limiti;
- [`scripts/output/inspect_dataset_out.txt`](scripts/output/inspect_dataset_out.txt): schema e dimensioni dei dataset usati nell'analisi.
