-- Migrate old category names to the current category system.
-- Edit the mappings below to match your old and new category names.

USE cityevents_db;

UPDATE events SET category = 'Film'    WHERE category IN ('Filmvisning', 'Biograffilm');
UPDATE events SET category = 'Teater'  WHERE category IN ('Scenkonst', 'Dramatik');
UPDATE events SET category = 'Musik'   WHERE category IN ('Konsert', 'Livemusik', 'Jazz', 'Folkmusik');
UPDATE events SET category = 'Musikal' WHERE category IN ('Musikteater');
UPDATE events SET category = 'Standup' WHERE category IN ('Humor', 'Improvisationsteater');
UPDATE events SET category = 'Dans'    WHERE category IN ('Dansföreställning');
UPDATE events SET category = 'Barn'    WHERE category IN ('Barnteater', 'Barnfilm', 'Familjeföreställning');
UPDATE events SET category = 'Övrigt'  WHERE category IN ('Lecture', 'Guidad tur', 'Poesi');

-- Set all NULL or empty categories to 'Övrigt'
UPDATE events SET category = 'Övrigt' WHERE category IS NULL OR category = '';

-- Show distribution after update
SELECT category, COUNT(*) as count
FROM events
GROUP BY category
ORDER BY count DESC;
