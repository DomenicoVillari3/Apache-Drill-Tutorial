-- ============================================================
-- Apache Drill — Demo Queries (livello 1→5)
-- Sorgenti: dfs (file system), pg (PostgreSQL), mongo (MongoDB)
-- ============================================================

-- -------------------------------------------------------
-- Query 1 — Schema-on-read su CSV (sorgente: dfs)
-- Trend ospedalizzazioni COVID per stato e settimana
-- -------------------------------------------------------
SELECT state,
       collection_week,
       SUM(CAST(inpatient_beds_used_covid AS BIGINT)) AS covid_beds
FROM dfs.healthdata.`covid/hospital_capacity.csv`
WHERE collection_week >= '2021-01-01'
GROUP BY state, collection_week
ORDER BY covid_beds DESC
LIMIT 20;

-- -------------------------------------------------------
-- Query 2 — Aggregazioni su PostgreSQL (sorgente: pg)
-- Top stati per pagamenti Medicare e numero di provider
-- -------------------------------------------------------
SELECT provider_state,
       COUNT(*)                                        AS num_providers,
       ROUND(AVG(average_medicare_payments), 2)        AS avg_payment
FROM pg.healthdata.medicare_providers
GROUP BY provider_state
ORDER BY avg_payment DESC
LIMIT 10;

-- -------------------------------------------------------
-- Query 3 — Documento annidato su MongoDB (sorgente: mongo)
-- Malattie notificabili per area con dot-notation
-- -------------------------------------------------------
SELECT t.reporting_area  AS state,
       t.disease_name,
       t.`current`.cases AS weekly_cases
FROM mongo.healthdata.nndss t
WHERE t.`current`.cases > 100
ORDER BY weekly_cases DESC
LIMIT 20;

-- -------------------------------------------------------
-- Query 4 — JOIN FEDERATO tra tutte e 3 le sorgenti
-- Una sola SELECT su CSV + PostgreSQL + MongoDB
-- -------------------------------------------------------
SELECT
    h.state,
    h.covid_beds,
    m.avg_payment       AS avg_medicare_payment,
    n.weekly_cases      AS notified_disease_cases

FROM (
    SELECT state,
           SUM(CAST(inpatient_beds_used_covid AS BIGINT)) AS covid_beds
    FROM dfs.healthdata.`covid/hospital_capacity.csv`
    WHERE collection_week = '2021-01-08'
    GROUP BY state
) h

JOIN (
    SELECT provider_state                           AS state,
           ROUND(AVG(average_medicare_payments), 2) AS avg_payment
    FROM pg.healthdata.medicare_providers
    GROUP BY provider_state
) m ON h.state = m.state

JOIN (
    SELECT t.reporting_area       AS state,
           SUM(t.`current`.cases) AS weekly_cases
    FROM mongo.healthdata.nndss t
    GROUP BY t.reporting_area
) n ON h.state = n.state

ORDER BY h.covid_beds DESC;

-- -------------------------------------------------------
-- Query 5 — EXPLAIN PLAN: CSV vs Parquet
-- Confronta il piano di esecuzione delle due sorgenti
-- -------------------------------------------------------

-- Baseline: CSV (row store)
EXPLAIN PLAN FOR
SELECT state,
       SUM(CAST(inpatient_beds_used_covid AS BIGINT))
FROM dfs.healthdata.`covid/hospital_capacity.csv`
GROUP BY state;

-- Ottimizzato: Parquet (columnar + predicate pushdown)
EXPLAIN PLAN FOR
SELECT state,
       SUM(inpatient_beds_used_covid)
FROM dfs.healthdata.`covid_parquet/hospital_capacity.parquet`
GROUP BY state;
