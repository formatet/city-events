-- city-events database schema

CREATE DATABASE IF NOT EXISTS cityevents_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE cityevents_db;

CREATE TABLE IF NOT EXISTS `events` (
    `id`            INT(11)         NOT NULL AUTO_INCREMENT,
    `title`         VARCHAR(500)    NOT NULL,
    `date`          DATETIME        NOT NULL,
    `venue`         VARCHAR(200)    NOT NULL,
    `category`      VARCHAR(100)    DEFAULT NULL,
    -- Valid categories: Film / Teater / Musik / Opera / Dans / Standup /
    --                   Klubb / Barn / Samtal / Poesi / Vernissage / Utställning / Övrigt
    `link`          TEXT            DEFAULT NULL,
    `description`   TEXT            DEFAULT NULL,
    `source`        VARCHAR(100)    DEFAULT NULL,
    -- source = scraper name, e.g. 'scrape_pustervik_db'. 'Manual' for admin events.
    `manual`        TINYINT(1)      DEFAULT 0,
    -- manual=1: never overwritten by scrapers, managed via /admin
    `featured`      TINYINT(1)      NOT NULL DEFAULT 0,
    -- featured=1: randomly selected event per calendar day (up to 24 days ahead)
    --             shown with accent-colour crystal icon in the UI
    `highlight`     VARCHAR(20)     DEFAULT NULL,
    -- highlight: visual variant for manual events
    --   'leftborder' = 3px gold left border
    --   'background' = warm beige background tint
    --   NULL = no highlight
    `crystal_color` VARCHAR(7)      DEFAULT NULL,
    -- crystal_color: custom crystal colour as hex (#bef2ff), overrides featured colour
    `created_at`    TIMESTAMP       NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`    TIMESTAMP       NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    -- updated_at is used by stale-cleanup: events not updated during a scrape run
    -- are automatically deleted (they have disappeared from the source)

    PRIMARY KEY (`id`),
    UNIQUE KEY `unique_event` (`title`, `date`, `venue`),
    KEY `idx_date`           (`date`),
    KEY `idx_venue`          (`venue`),
    KEY `idx_category`       (`category`),
    KEY `idx_source`         (`source`),
    KEY `idx_date_venue`     (`date`, `venue`),
    KEY `idx_source_updated` (`source`, `updated_at`),
    KEY `idx_featured`       (`featured`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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

-- Create a dedicated database user (replace password with something secure)
-- CREATE USER IF NOT EXISTS 'cityevents'@'localhost' IDENTIFIED BY 'your-password-here';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON cityevents_db.events TO 'cityevents'@'localhost';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON cityevents_db.pending_submissions TO 'cityevents'@'localhost';
-- FLUSH PRIVILEGES;
