-- RobinHood AI Database Setup
-- Run this script to create the database and tables

CREATE DATABASE IF NOT EXISTS robinhood_db;
USE robinhood_db;

-- Users/Taxpayers table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) UNIQUE NOT NULL,
    declared_income DECIMAL(15, 2) NOT NULL DEFAULT 0,
    tax_paid DECIMAL(15, 2) NOT NULL DEFAULT 0,
    flagged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tax notices table
CREATE TABLE IF NOT EXISTS notices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    notice_type ENUM('reminder', 'warning', 'final', 'penalty') NOT NULL,
    amount_due DECIMAL(15, 2) NOT NULL,
    message TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Payments table
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    reference_no VARCHAR(100),
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Insert sample data
INSERT INTO users (user_id, declared_income, tax_paid, flagged) VALUES
('TXP001', 500000, 10000, FALSE),
('TXP002', 800000, 25000, FALSE),
('TXP003', 1200000, 45000, FALSE),
('TXP004', 1500000, 90000, FALSE),
('TXP005', 2000000, 100000, TRUE),
('TXP006', 350000, 0, FALSE),
('TXP007', 950000, 55000, FALSE),
('TXP008', 600000, 15000, FALSE)
ON DUPLICATE KEY UPDATE user_id=user_id;

SELECT 'Database setup complete!' as Status;