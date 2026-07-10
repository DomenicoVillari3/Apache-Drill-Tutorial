# Apache Drill come Query Federation Engine — Tutorial

> Scheletro del report. Ogni sezione riporta solo i punti fondamentali da sviluppare.

---

## 1. Introduzione

- Cos'e' Apache Drill in una frase (SQL engine per query federate, schema-on-read, no ETL)
- Il problema che risolve: dati sparsi su piu' sistemi (file, RDBMS, NoSQL) normalmente richiedono ETL prima di poterli incrociare
- Dominio applicativo: dataset COVID-19 di HealthData.gov (U.S. HHS)
- Domanda di ricerca guida (vedi CLAUDE.md, sezione "Filo narrativo analitico")
- Cosa dimostra il tutorial: 1 query SQL su 3 sistemi eterogenei, senza spostare un byte

## 2. Architettura del sistema

- Diagramma dei 4 servizi Docker: drill, postgres, mongo, jupyter (rete `health-net`)
- Ruolo di ciascun servizio in una riga
- Concetto chiave: Drill non e' un database, e' un **motore di query distribuito** che si collega ad altri sistemi via *storage plugin*
- I 3 plugin usati: `dfs` (filesystem), `pg` (JDBC/PostgreSQL), `mongo` (MongoDB) — chiarire che CSV e Parquet sono due formati sotto lo stesso plugin `dfs`, non due sorgenti diverse

## 3. I 5 dataset e la loro distribuzione

- Tabella riassuntiva: dataset → sorgente → motivazione della scelta (schema, granularita', volume)
- Dataset 1 — Hospital Capacity (CSV + Parquet, `dfs`)
- Dataset 2 — Estimated Beds (PostgreSQL, `pg`)
- Dataset 3 — Therapeutic Locator (MongoDB, `mongo`)
- Dataset 4 — Community Profile / county-level (CSV, `dfs`)
- Dataset 5 — Treatments / therapeutic sites (CSV, `dfs`)
- Nota su provenienza: download manuale da healthdata.gov (limite API Socrata 1000 righe)

## 4. Setup dell'ambiente

- Prerequisiti (Docker Desktop)
- `docker-compose.yml`: i 4 servizi, healthcheck, rete condivisa
- Nota sul driver JDBC PostgreSQL: montato come volume in `docker-compose.yml` (non serve piu' `docker cp` manuale)
- Comando di avvio e verifica (`docker-compose up -d`, `docker-compose ps`)
- Primo test sulla Drill Web UI (`localhost:8047`, `SELECT * FROM sys.version`)

## 5. Preparazione dei dati

- Perche' alcuni dataset vanno "puliti" prima del caricamento e altri no (distinzione voluta: Dataset 1 e 4 restano grezzi per dimostrare lo schema-on-read; Dataset 2/3/5 vengono normalizzati prima di andare su Postgres/Mongo/dfs)
- `scripts/normalize_columns.py`: rinomina colonne mixed-case/spazi → snake_case, produce i file `*_clean.csv`
- Problema riscontrato: separatore delle migliaia (virgola) nei numeri del CSV grezzo → soluzione nella query (`REPLACE`+`NULLIF`), non nel dato
- `scripts/csv_to_parquet.py`: conversione Dataset 1 in Parquet con pyarrow, stesso problema delle virgole risolto lato script (`pd.to_numeric` dopo pulizia)
- Numeri chiave: dimensione CSV vs Parquet, ratio di compressione

## 6. Caricamento nelle sorgenti

- PostgreSQL: `init-sql/01_load_estimated_beds.sql` — CREATE TABLE + COPY, verifica con COUNT(*)
- MongoDB: `init-mongo/01_load_therapeutic.py` — import collection, verifica con countDocuments()
- Filesystem: nessun caricamento, i CSV/Parquet restano su disco in `./data/`

## 7. Configurazione dei plugin Drill

- Dove si configurano (Web UI → Storage, oppure file JSON montato come override)
- Plugin `dfs`: workspace `healthdata`, formati csv/parquet
- Plugin `pg`: connection string JDBC, credenziali
- Plugin `mongo`: connection string, credenziali
- Verifica di ciascun plugin con una query `LIMIT 5`

## 8. Le query dimostrative — livello base

- Query 1 — schema-on-read su CSV grezzo (`dfs`)
- Query 2 — aggregazioni su PostgreSQL (`pg`)
- Query 3 — flessibilita' di schema su MongoDB (`mongo`)
- Per ciascuna: cosa dimostra, snippet SQL, un risultato/numero significativo

## 9. Il join federato — costruzione incrementale

- Perche' costruire il join a piccoli passi invece che mostrare subito la query complessa
- Join a 2 vie: dfs+pg, dfs+mongo, pg+mongo (dati pre-aggregati per stato)
- Join a 3 vie: dfs+pg+mongo (la query "chiave" del progetto)
- Join intensivo a livello di riga: stessa unione ma su chiave stato+data, senza pre-aggregazione — cosa cambia nel piano di esecuzione e nei tempi
- Nota tecnica sul join tra tipi data diversi (`VARCHAR` su dfs vs `DATE` su pg, `TO_DATE`)
- Tabella/grafico dei tempi di esecuzione per ciascuno step

## 10. CSV vs Parquet — perche' il formato conta

- `EXPLAIN PLAN FOR`: lettura del piano fisico, differenza principale (step di `CAST`/`REPLACE` assente su Parquet)
- Confronto tempi reali di esecuzione (media su piu' run)
- Interpretazione: columnar storage, meno I/O, meno parsing, statistiche per colonna

## 11. Query multi-scala e complementari

- Query 6 — join stato/contea sullo stesso plugin `dfs` (Dataset 1 + 4)
- Query 7 — disponibilita' terapie per sede (Dataset 5)
- Cosa aggiungono alla narrazione principale

## 12. Il notebook Jupyter

- Perche' usare la REST API di Drill invece del JDBC (`requests` verso `query.json`)
- Struttura del notebook: helper di query con timing, esecuzione incrementale, grafici
- Grafici principali prodotti: top stati nel join federato, CSV vs Parquet, costo incrementale dei join, riepilogo tempi per categoria
- Come rieseguirlo (`jupyter nbconvert --execute` o dalla UI su `localhost:8888`)

## 13. Risultati e osservazioni

- Riepilogo numerico: righe per sorgente, tempi per query/categoria, speedup Parquet
- Bug/problemi incontrati e come sono stati risolti (virgole nei numeri, NULL first in ORDER BY, join di tipi data eterogenei) — utile come sezione "cosa puo' andare storto"
- Limiti del setup (nessun pushdown del join, dimensione dei dati ridotta rispetto a un caso reale, ambiente locale single-node)

## 14. Conclusioni

- Risposta alla domanda di ricerca iniziale
- Quando ha senso usare Drill in un caso reale (e quando no)
- Possibili estensioni (piu' nodi Drill, piu' formati, caching dei metadati, integrazione BI)

## Appendice

- Elenco comandi principali (`commands.txt`)
- Struttura directory del progetto
- Query SQL complete (rimando a `queries/demo_queries.sql`)
