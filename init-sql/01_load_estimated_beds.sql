CREATE SCHEMA IF NOT EXISTS healthdata;

DROP TABLE IF EXISTS healthdata.estimated_beds;

CREATE TABLE healthdata.estimated_beds (
    state                 CHAR(2),
    collection_date       DATE,
    estimated_beds_covid  NUMERIC,
    count_ll              NUMERIC,
    count_ul              NUMERIC,
    pct_beds_covid        NUMERIC,
    pct_ll                NUMERIC,
    pct_ul                NUMERIC,
    total_inpatient_beds  NUMERIC,
    total_ll              NUMERIC,
    total_ul              NUMERIC,
    geocoded_state        TEXT
);
