-- Migration: add 'manual' column to events table
-- Run this on an existing database to upgrade from an earlier schema version.

USE cityevents_db;

ALTER TABLE events ADD COLUMN IF NOT EXISTS manual BOOLEAN DEFAULT FALSE AFTER source;

DESCRIBE events;
