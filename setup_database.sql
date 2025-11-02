CREATE DATABASE IF NOT EXISTS robinhood_db;
USE robinhood_db;
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(255) PRIMARY KEY,
    declared_income DECIMAL(10, 2) NOT NULL,
    observed_transactions TEXT,
    income_source VARCHAR(255),
    tax_paid DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    flagged BOOLEAN NOT NULL DEFAULT FALSE
);
