-- Migration to fix muscle column naming inconsistency
-- The initial schema defines 'primary_muscle' but migration 005 adds 'muscle_group'
-- This migration ensures the database schema is consistent

-- Ensure muscle_group column exists and has correct type
ALTER TABLE exercises ADD COLUMN IF NOT EXISTS muscle_group VARCHAR(100);

-- If both columns exist, sync primary_muscle to muscle_group
UPDATE exercises 
SET muscle_group = COALESCE(muscle_group, primary_muscle, 'unknown')
WHERE muscle_group IS NULL OR muscle_group = '';

-- Drop primary_muscle if it exists (to avoid confusion)
-- Note: Only do this if we've successfully migrated the data above
-- ALTER TABLE exercises DROP COLUMN IF EXISTS primary_muscle;

-- Ensure muscle_group is NOT NULL
ALTER TABLE exercises 
MODIFY COLUMN muscle_group VARCHAR(100) NOT NULL DEFAULT 'unknown';
