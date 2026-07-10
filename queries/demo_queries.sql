-- ============================================================
-- Apache Drill — Demo Queries (livello 1→7)
-- Sorgenti: dfs (file system), pg (PostgreSQL), mongo (MongoDB)
-- Colonne verificate live sulle 3 sorgenti il 2026-07-10.
-- Note:
--  - "date" e' parola riservata in Drill -> va tra backtick.
--  - inpatient_beds_used_covid (CSV grezzo, Dataset 1) contiene
--    virgole come separatore delle migliaia (es. "1,338") e valori
--    vuoti: va ripulito con REPLACE + NULLIF prima del CAST.
--    Il file resta grezzo di proposito, per dimostrare lo
--    schema-on-read di Drill (stesso problema corretto anche in
--    scripts/csv_to_parquet.py per la versione Parquet).
-- ============================================================

-- -------------------------------------------------------
-- Query 1 — Schema-on-read su CSV (sorgente: dfs / Dataset 1)
-- Trend ospedalizzazioni COVID per stato e data
-- -------------------------------------------------------
SELECT state,
       `date`,
       SUM(CAST(NULLIF(REPLACE(inpatient_beds_used_covid, ',', ''), '') AS BIGINT)) AS covid_beds_used
FROM dfs.healthdata.`covid/hospital_capacity.csv`
WHERE `date` >= '2021/01/01'
GROUP BY state, `date`
ORDER BY covid_beds_used DESC
LIMIT 20;

-- -------------------------------------------------------
-- Query 2 — Aggregazioni su PostgreSQL (sorgente: pg / Dataset 2)
-- Occupazione stimata letti COVID per stato (media nel periodo)
-- -------------------------------------------------------
SELECT state,
       COUNT(*)                              AS num_observations,
       ROUND(AVG(estimated_beds_covid), 0)   AS avg_estimated_beds_covid,
       ROUND(AVG(pct_beds_covid), 4)         AS avg_pct_covid
FROM pg.healthdata.estimated_beds
GROUP BY state
ORDER BY avg_estimated_beds_covid DESC
LIMIT 10;

-- -------------------------------------------------------
-- Query 3 — Flessibilita' di schema su MongoDB (sorgente: mongo / Dataset 3)
-- Centri terapeutici attivi per stato e farmaco distribuito
-- -------------------------------------------------------
SELECT t.state,
       t.order_label     AS therapy_name,
       COUNT(*)          AS num_centers
FROM mongo.healthdata.therapeutic t
WHERE t.provider_status = 'ACTIVE'
GROUP BY t.state, t.order_label
ORDER BY num_centers DESC
LIMIT 20;

-- -------------------------------------------------------
-- Query 4 — JOIN FEDERATO tra tutte e 3 le sorgenti (la query chiave)
-- Capacita' ospedaliera (CSV) + stime letti (PostgreSQL)
-- + centri terapeutici attivi (MongoDB) per stato — senza ETL
-- -------------------------------------------------------
SELECT
    h.state,
    h.covid_beds_used,
    e.avg_estimated_beds_covid,
    c.num_therapy_centers

FROM (
    SELECT state,
           SUM(CAST(NULLIF(REPLACE(inpatient_beds_used_covid, ',', ''), '') AS BIGINT)) AS covid_beds_used
    FROM dfs.healthdata.`covid/hospital_capacity.csv`
    WHERE `date` = '2021/07/09'
    GROUP BY state
) h

JOIN (
    SELECT state,
           ROUND(AVG(estimated_beds_covid), 0) AS avg_estimated_beds_covid
    FROM pg.healthdata.estimated_beds
    GROUP BY state
) e ON h.state = e.state

JOIN (
    SELECT t.state,
           COUNT(*) AS num_therapy_centers
    FROM mongo.healthdata.therapeutic t
    WHERE t.provider_status = 'ACTIVE'
    GROUP BY t.state
) c ON h.state = c.state

ORDER BY h.covid_beds_used DESC;

-- -------------------------------------------------------
-- Query 5 — EXPLAIN PLAN + confronto CSV vs Parquet (sorgente: dfs)
-- -------------------------------------------------------

-- Baseline: CSV (row store)
EXPLAIN PLAN FOR
SELECT state,
       SUM(CAST(NULLIF(REPLACE(inpatient_beds_used_covid, ',', ''), '') AS BIGINT))
FROM dfs.healthdata.`covid/hospital_capacity.csv`
GROUP BY state;

-- Ottimizzato: Parquet (columnar + predicate pushdown)
EXPLAIN PLAN FOR
SELECT state,
       SUM(inpatient_beds_used_covid)
FROM dfs.healthdata.`covid_parquet/hospital_capacity.parquet`
GROUP BY state;

-- -------------------------------------------------------
-- Query 6 — Multi-scala: stato + contea sullo stesso plugin dfs
-- (Dataset 1 + Dataset 4)
-- -------------------------------------------------------
SELECT s.state,
       s.covid_beds_used   AS state_covid_beds,
       c.county,
       c.cases_last_7_days AS county_cases_7d
FROM (
    SELECT state,
           SUM(CAST(NULLIF(REPLACE(inpatient_beds_used_covid, ',', ''), '') AS BIGINT)) AS covid_beds_used
    FROM dfs.healthdata.`covid/hospital_capacity.csv`
    WHERE `date` = '2021/07/09'
    GROUP BY state
) s
JOIN dfs.healthdata.`county/community_profile.csv` c
  ON s.state = c.state
ORDER BY state_covid_beds DESC, county_cases_7d DESC
LIMIT 30;

-- -------------------------------------------------------
-- Query 7 — Disponibilita' terapie per sede (sorgente: dfs / Dataset 5)
-- Quante sedi per stato offrono Paxlovid, Lagevrio e Veklury
-- -------------------------------------------------------
SELECT state,
       SUM(CASE WHEN has_paxlovid = 'true' THEN 1 ELSE 0 END) AS sites_with_paxlovid,
       SUM(CASE WHEN has_lagevrio = 'true' THEN 1 ELSE 0 END) AS sites_with_lagevrio,
       SUM(CASE WHEN has_veklury  = 'true' THEN 1 ELSE 0 END) AS sites_with_veklury,
       COUNT(*)                                                AS total_sites
FROM dfs.healthdata.`treatments/treatments_clean.csv`
GROUP BY state
ORDER BY total_sites DESC
LIMIT 20;
