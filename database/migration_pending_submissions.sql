-- Migration: lägg till pending_submissions-tabell för crowdsourcade anmälningar

USE kristall_db;

CREATE TABLE IF NOT EXISTS `pending_submissions` (
    `id`            INT AUTO_INCREMENT PRIMARY KEY,
    `title`         VARCHAR(500) NOT NULL,
    `event_date`    DATE NOT NULL,
    `event_time`    TIME DEFAULT NULL,
    `venue`         VARCHAR(200) NOT NULL,
    `category`      VARCHAR(100) NOT NULL,
    `link`          TEXT DEFAULT NULL,
    `description`   TEXT DEFAULT NULL,
    `contact_email` VARCHAR(255) DEFAULT NULL,
    `submitted_at`  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
