CREATE SCHEMA IF NOT EXISTS healthdata;

CREATE TABLE IF NOT EXISTS healthdata.medicare_providers (
    npi                       VARCHAR(20),
    provider_last_name        TEXT,
    provider_first_name       TEXT,
    provider_state            CHAR(2),
    provider_type             TEXT,
    total_services            NUMERIC,
    total_unique_benes        NUMERIC,
    average_medicare_payments NUMERIC
);

